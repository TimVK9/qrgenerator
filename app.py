from flask import Flask, render_template, request, jsonify, send_file
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from io import BytesIO
import base64
import re
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

# Добавляем заголовки CORS для разработки
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
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
    '#00b09b', '#FF5733', '#33FF57', '#3357FF', '#FF33F6', '#F0FF33'
]

# Уровни коррекции ошибок
ERROR_CORRECTION_LEVELS = {
    'L': {'name': 'L (Низкий, 7%)', 'const': ERROR_CORRECT_L},
    'M': {'name': 'M (Средний, 15%)', 'const': ERROR_CORRECT_M},
    'Q': {'name': 'Q (Высокий, 25%)', 'const': ERROR_CORRECT_Q},
    'H': {'name': 'H (Максимальный, 30%)', 'const': ERROR_CORRECT_H}
}

def get_max_chars_for_size(size_id, error_level='M'):
    """Получает максимальное количество символов для размера и уровня коррекции."""
    size_info = next((s for s in SIZE_OPTIONS if s['id'] == size_id), SIZE_OPTIONS[2])
    return size_info['char_limits'].get(error_level, '~240 символов')

def validate_color(color):
    """Проверяет и валидирует цвет в формате HEX."""
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
    """Оптимизирует введенные данные для QR-кода."""
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
    qr_data_url = None
    qr_info = None
    form_data = {}
    warning_message = None
    
    if request.method == 'POST':
        try:
            data = request.form.get('data', '').strip()
            if not data:
                return render_template('index.html',
                                    size_options=SIZE_OPTIONS,
                                    color_options=COLOR_OPTIONS,
                                    error="Пожалуйста, введите данные для QR-кода",
                                    form_data=request.form)
            
            optimized_data = optimize_data(data)
            
            size_id = request.form.get('size', 'm')
            selected_size = next((s for s in SIZE_OPTIONS if s['id'] == size_id), SIZE_OPTIONS[2])
            
            color = validate_color(request.form.get('color', '#000000'))
            error_correction = request.form.get('error_correction', 'M')
            
            # Проверяем длину данных
            data_length = len(data)
            max_chars = get_max_chars_for_size(size_id, error_correction)
            
            # Получаем уровень коррекции ошибок
            error_correction_info = ERROR_CORRECTION_LEVELS.get(error_correction, ERROR_CORRECTION_LEVELS['M'])
            
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
                warning_message = f"Внимание: данные ({data_length} символов) могут не поместиться в выбранный размер с уровнем коррекции {error_correction}. Рекомендуется выбрать больший размер или более высокий уровень коррекции."
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
            qr_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
            
            # Информация о QR-коде для отображения
            qr_info = {
                'data': data,
                'optimized_data': optimized_data,
                'data_length': data_length,
                'selected_size': selected_size,
                'color': color,
                'error_level': error_correction_info['name'],
                'size_px': (
                    qr.modules_count * selected_size['box_size'] + 2 * selected_size['border'] * selected_size['box_size'],
                    qr.modules_count * selected_size['box_size'] + 2 * selected_size['border'] * selected_size['box_size']
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
            return render_template('index.html',
                                size_options=SIZE_OPTIONS,
                                color_options=COLOR_OPTIONS,
                                error=f"Ошибка при генерации QR-кода: {str(e)}",
                                form_data=request.form)
    
    return render_template('index.html',
                          size_options=SIZE_OPTIONS,
                          color_options=COLOR_OPTIONS,
                          qr_data_url=qr_data_url,
                          qr_info=qr_info,
                          form_data=form_data,
                          warning_message=warning_message)

@app.route('/health')
def health_check():
    """Эндпоинт для проверки здоровья приложения."""
    return jsonify({'status': 'healthy', 'service': 'qr-generator'}), 200

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint for generating QR codes."""
    try:
        data = request.json.get('data', '').strip()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        size_id = request.json.get('size', 'm')
        color = validate_color(request.json.get('color', '#000000'))
        error_correction = request.json.get('error_correction', 'M')
        
        selected_size = next((s for s in SIZE_OPTIONS if s['id'] == size_id), SIZE_OPTIONS[2])
        error_correction_info = ERROR_CORRECTION_LEVELS.get(error_correction, ERROR_CORRECTION_LEVELS['M'])
        
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
        qr_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        
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

@app.route('/robots.txt')
def robots():
    """Файл robots.txt для SEO."""
    return """User-agent: *
Allow: /"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)