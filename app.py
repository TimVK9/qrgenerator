from flask import (
    Flask,
    send_from_directory,
    render_template,
    request,
    jsonify,
    send_file
)
import qrcode
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H
)
from io import BytesIO
import base64
import re
import os
import secrets
from datetime import timedelta

app = Flask(__name__)

# Конфигурация приложения
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(days=1),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
)


def get_csp_for_request():
    """
    Возвращает Content Security Policy для текущего запроса.
    """
    base_csp = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "img-src 'self' data: https:",
        "font-src 'self' https://cdn.jsdelivr.net",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "object-src 'none'",
    ]
    
    return '; '.join(base_csp)


@app.after_request
def add_security_headers(response):
    """
    Добавляет security headers к каждому ответу.
    """
    # Удаляем лишние заголовки
    headers_to_remove = ['X-Powered-By', 'Server']
    for header in headers_to_remove:
        if header in response.headers:
            del response.headers[header]
    
    # Базовые заголовки безопасности
    response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '0',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': (
            'accelerometer=(), autoplay=(), camera=(), '
            'geolocation=(), gyroscope=(), magnetometer=(), '
            'microphone=(), payment=(), usb=()'
        ),
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Resource-Policy': 'same-origin',
        'X-DNS-Prefetch-Control': 'off',
    })
    
    # HSTS для продакшена
    if os.environ.get('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = get_csp_for_request()
    
    # Настройки кэширования
    if request.path.startswith('/static/'):
        # Статические файлы - длительное кэширование
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    else:
        # Динамические страницы - не кэшировать
        response.headers['Cache-Control'] = (
            'no-store, no-cache, must-revalidate, proxy-revalidate'
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    # CORS заголовки для API
    if request.path.startswith('/api/'):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response


# Настройки размеров с информацией об ограничениях
SIZE_OPTIONS = [
    {
        'id': 'xs',
        'name': 'Очень маленький',
        'box_size': 5,
        'border': 2,
        'desc': 'Для очень плотной печати',
        'icon': 'bi-qr-code-scan',
        'char_limits': {
            'L': '~100 символов',
            'M': '~80 символов',
            'Q': '~60 символов',
            'H': '~40 символов'
        },
        'max_version': 10
    },
    {
        'id': 's',
        'name': 'Маленький',
        'box_size': 8,
        'border': 3,
        'desc': 'Для документов и визиток',
        'icon': 'bi-qr-code',
        'char_limits': {
            'L': '~200 символов',
            'M': '~160 символов',
            'Q': '~120 символов',
            'H': '~80 символов'
        },
        'max_version': 20
    },
    {
        'id': 'm',
        'name': 'Средний',
        'box_size': 10,
        'border': 4,
        'desc': 'Универсальный размер',
        'icon': 'bi-qr-code',
        'char_limits': {
            'L': '~300 символов',
            'M': '~240 символов',
            'Q': '~180 символов',
            'H': '~120 символов'
        },
        'max_version': 30
    },
    {
        'id': 'l',
        'name': 'Большой',
        'box_size': 15,
        'border': 5,
        'desc': 'Для плакатов и дисплеев',
        'icon': 'bi-qr-code-scan',
        'char_limits': {
            'L': '~500 символов',
            'M': '~400 символов',
            'Q': '~300 символов',
            'H': '~200 символов'
        },
        'max_version': 40
    },
    {
        'id': 'xl',
        'name': 'Очень большой',
        'box_size': 20,
        'border': 6,
        'desc': 'Для больших дисплеев и баннеров',
        'icon': 'bi-qr-code-scan',
        'char_limits': {
            'L': '~700 символов',
            'M': '~550 символов',
            'Q': '~400 символов',
            'H': '~280 символов'
        },
        'max_version': 40
    }
]

# Цветовая палитра
COLOR_OPTIONS = [
    '#000000', '#6c63ff', '#ff6584', '#36d1dc', '#ff9966',
    '#59c173', '#a17fe0', '#4a00e0', '#ff416c', '#5d26c1',
    '#00b09b', '#FF5733', '#33FF57', '#3357FF', '#FF33F6',
    '#F0FF33'
]

# Уровни коррекции ошибок
ERROR_CORRECTION_LEVELS = {
    'L': {'name': 'L (Низкий, 7%)', 'const': ERROR_CORRECT_L},
    'M': {'name': 'M (Средний, 15%)', 'const': ERROR_CORRECT_M},
    'Q': {'name': 'Q (Высокий, 25%)', 'const': ERROR_CORRECT_Q},
    'H': {'name': 'H (Максимальный, 30%)', 'const': ERROR_CORRECT_H}
}


def get_max_chars_for_size(size_id, error_level='M'):
    """
    Получает максимальное количество символов для размера и уровня коррекции.
    """
    size_info = next(
        (s for s in SIZE_OPTIONS if s['id'] == size_id),
        SIZE_OPTIONS[2]
    )
    return size_info['char_limits'].get(error_level, '~240 символов')


def validate_color(color):
    """
    Проверяет и валидирует цвет в формате HEX.
    """
    if not color:
        return '#000000'
    
    color = color.strip()
    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    
    if re.match(hex_pattern, color):
        if len(color) == 4:
            color = f'#{color[1]*2}{color[2]*2}{color[3]*2}'
        return color
    
    if color in COLOR_OPTIONS:
        return color
    
    return '#000000'


def optimize_data(data):
    """
    Оптимизирует введенные данные для QR-кода.
    """
    data = data.strip()
    
    # Проверяем на email
    if '@' in data and '.' in data and not data.startswith('mailto:'):
        if ' ' not in data and not data.startswith('http'):
            return f'mailto:{data}'
    
    # Проверяем на телефон
    phone_pattern = r'^[\d\s\-\+\(\)]+$'
    if re.match(phone_pattern, data) and len(data.replace(' ', '')) >= 10:
        if not data.startswith('tel:'):
            cleaned = re.sub(r'[^\d\+]', '', data)
            return f'tel:{cleaned}'
    
    # Проверяем на URL
    if not data.startswith(('http://', 'https://', 'mailto:', 'tel:')):
        url_pattern = r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}'
        if re.match(url_pattern, data):
            return f'https://{data}'
    
    return data


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Главная страница с генератором QR-кодов.
    """
    qr_data_url = None
    qr_info = None
    form_data = {}
    warning_message = None
    
    if request.method == 'POST':
        try:
            data = request.form.get('data', '').strip()
            if not data:
                return render_template(
                    'index.html',
                    size_options=SIZE_OPTIONS,
                    color_options=COLOR_OPTIONS,
                    error="Пожалуйста, введите данные для QR-кода",
                    form_data=request.form
                )
            
            optimized_data = optimize_data(data)
            
            size_id = request.form.get('size', 'm')
            selected_size = next(
                (s for s in SIZE_OPTIONS if s['id'] == size_id),
                SIZE_OPTIONS[2]
            )
            
            color = validate_color(request.form.get('color', '#000000'))
            error_correction = request.form.get('error_correction', 'M')
            
            # Проверяем длину данных
            data_length = len(data)
            max_chars = get_max_chars_for_size(size_id, error_correction)
            
            # Получаем уровень коррекции ошибок
            error_correction_info = ERROR_CORRECTION_LEVELS.get(
                error_correction,
                ERROR_CORRECTION_LEVELS['M']
            )
            
            # Создаем QR-код с цветом
            qr = qrcode.QRCode(
                version=1,
                error_correction=error_correction_info['const'],
                box_size=selected_size['box_size'],
                border=selected_size['border']
            )
            
            qr.add_data(optimized_data)
            
            try:
                qr.make(fit=True)
            except qrcode.exceptions.DataOverflowError:
                warning_message = (
                    f"Внимание: данные ({data_length} символов) могут не "
                    f"поместиться в выбранный размер с уровнем коррекции "
                    f"{error_correction}. Рекомендуется выбрать больший "
                    "размер или более высокий уровень коррекции."
                )
                # Пытаемся сгенерировать с автоматическим подбором версии
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=error_correction_info['const'],
                    box_size=selected_size['box_size'],
                    border=selected_size['border']
                )
                qr.add_data(optimized_data)
                qr.make(fit=True)
            
            # Создаем изображение с выбранным цветом
            qr_img = qr.make_image(fill_color=color, back_color="white")
            
            # Сохраняем в буфер
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Конвертируем в base64 для отображения на странице
            qr_data_url = (
                f"data:image/png;base64,"
                f"{base64.b64encode(buffer.getvalue()).decode()}"
            )
            
            # Информация о QR-коде для отображения
            qr_info = {
                'data': data,
                'optimized_data': optimized_data,
                'data_length': data_length,
                'selected_size': selected_size,
                'color': color,
                'error_level': error_correction_info['name'],
                'size_px': (
                    qr.modules_count * selected_size['box_size'] +
                    2 * selected_size['border'] * selected_size['box_size'],
                    qr.modules_count * selected_size['box_size'] +
                    2 * selected_size['border'] * selected_size['box_size']
                ),
                'version': qr.version,
                'max_chars': max_chars
            }
            
            # Сохраняем данные формы для повторного отображения
            form_data = {
                'data': data,
                'size': size_id,
                'color': color,
                'error_correction': error_correction
            }
            
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return render_template(
                'index.html',
                size_options=SIZE_OPTIONS,
                color_options=COLOR_OPTIONS,
                error=f"Ошибка при генерации QR-кода: {str(e)}",
                form_data=request.form
            )
    
    return render_template(
        'index.html',
        size_options=SIZE_OPTIONS,
        color_options=COLOR_OPTIONS,
        qr_data_url=qr_data_url,
        qr_info=qr_info,
        form_data=form_data,
        warning_message=warning_message
    )


@app.route('/health')
def health_check():
    """
    Эндпоинт для проверки здоровья приложения.
    """
    return jsonify({'status': 'healthy', 'service': 'qr-generator'}), 200


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    API endpoint for generating QR codes.
    """
    try:
        data = request.json.get('data', '').strip()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        size_id = request.json.get('size', 'm')
        color = validate_color(request.json.get('color', '#000000'))
        error_correction = request.json.get('error_correction', 'M')
        
        selected_size = next(
            (s for s in SIZE_OPTIONS if s['id'] == size_id),
            SIZE_OPTIONS[2]
        )
        error_correction_info = ERROR_CORRECTION_LEVELS.get(
            error_correction,
            ERROR_CORRECTION_LEVELS['M']
        )
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=error_correction_info['const'],
            box_size=selected_size['box_size'],
            border=selected_size['border']
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(fill_color=color, back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Convert to base64
        qr_data_url = (
            f"data:image/png;base64,"
            f"{base64.b64encode(buffer.getvalue()).decode()}"
        )
        
        return jsonify({
            'success': True,
            'qr_code': qr_data_url,
            'info': {
                'data_length': len(data),
                'size': selected_size['name'],
                'color': color,
                'error_correction': error_correction_info['name']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Security files
@app.route('/.well-known/security.txt')
@app.route('/security.txt')
def security_txt():
    """
    Возвращает файл security.txt.
    """
    return send_from_directory('static', 'security.txt'), 200, {
        'Content-Type': 'text/plain; charset=utf-8'
    }


# Policy pages
@app.route('/privacy-policy')
@app.route('/privacy')
def privacy_policy():
    """
    Страница политики конфиденциальности.
    """
    return render_template('privacy-policy.html')


@app.route('/terms-of-service')
@app.route('/terms')
def terms_of_service():
    """
    Страница условий использования.
    """
    return render_template('terms-of-service.html')


@app.route('/cookie-policy')
@app.route('/cookies')
def cookie_policy():
    """
    Страница политики использования cookies.
    """
    return render_template('cookie-policy.html')


@app.route('/dmca-policy')
def dmca_policy():
    """
    Страница DMCA политики.
    """
    return render_template('dmca-policy.html')


# Static files
@app.route('/ads.txt')
def ads_txt():
    """
    Возвращает ads.txt файл.
    """
    return send_from_directory('static', 'ads.txt'), 200, {
        'Content-Type': 'text/plain; charset=utf-8'
    }


@app.route('/robots.txt')
def robots_txt():
    """
    Возвращает robots.txt файл.
    """
    return send_from_directory('static', 'robots.txt'), 200, {
        'Content-Type': 'text/plain; charset=utf-8'
    }


@app.route('/sitemap.xml')
def sitemap_xml():
    """
    Возвращает sitemap.xml файл.
    """
    return send_from_directory('static', 'sitemap.xml'), 200, {
        'Content-Type': 'application/xml; charset=utf-8'
    }


# Humans.txt (опционально)
@app.route('/humans.txt')
def humans_txt():
    """
    Возвращает humans.txt файл.
    """
    return send_from_directory('static', 'humans.txt'), 200, {
        'Content-Type': 'text/plain; charset=utf-8'
    }

@app.route('/yandex_9dec845bb9d3d77e.html')
def yandex_verification():
    """Яндекс.Вебмастер подтверждение прав на сайт"""
    return '''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        </head>
        <body>Verification: 9dec845bb9d3d77e</body>
    </html>
    ''', 200



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Для локальной разработки
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )