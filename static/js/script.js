// Обработчик глобальных ошибок
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('Global error:', {msg, url, lineNo, columnNo, error});
    return false;
};

// Отключаем вывод console.log в продакшн
if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    console.log = function() {};
    console.debug = function() {};
}
// Глобальные переменные
let colorInput, customColorInput, customColorHex, applyColorBtn;
let dataInput, charCountElement, maxCharsInfoElement, charProgressElement;
let formSubmitted = false;
let currentQRDataUrl = null;

/**
 * Инициализация при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('QR Генератор: Инициализация...');
    
    try {
        initElements();
        initColorSystem();
        initSizeButtons();
        initFormValidation();
        initCharCounter();
        initHexColorInput();
        initEventListeners();
        
        checkForQRResult();
        
        console.log('Инициализация завершена успешно');
    } catch (error) {
        console.error('Ошибка при инициализации:', error);
        showNotification('Ошибка инициализации приложения', 'error');
    }
});

/**
 * Инициализация DOM элементов
 */
function initElements() {
    colorInput = document.getElementById('colorInput');
    customColorInput = document.getElementById('customColorInput');
    customColorHex = document.getElementById('customColorHex');
    applyColorBtn = document.getElementById('applyColorBtn');
    
    dataInput = document.getElementById('dataInput');
    charCountElement = document.getElementById('charCount');
    maxCharsInfoElement = document.getElementById('maxCharsInfo');
    charProgressElement = document.getElementById('charProgress');
}

/**
 * Инициализация системы цветов
 */
function initColorSystem() {
    if (!colorInput || !customColorInput || !customColorHex) {
        console.warn('Элементы цвета не найдены');
        return;
    }
    
    const initialColor = colorInput.value || '#000000';
    
    customColorInput.value = initialColor;
    customColorHex.value = initialColor;
    
    console.log('Система цветов инициализирована с цветом:', initialColor);
}

/**
 * Инициализация HEX поля ввода
 */
function initHexColorInput() {
    if (!customColorHex) return;
    
    customColorHex.addEventListener('input', function() {
        let value = this.value.trim();
        
        // Добавляем # если его нет
        if (value && !value.startsWith('#')) {
            value = '#' + value;
        }
        
        // Фильтруем недопустимые символы
        value = value.replace(/[^#0-9A-Fa-f]/g, '');
        
        // Ограничиваем длину
        if (value.length > 7) {
            value = value.substring(0, 7);
        }
        
        this.value = value;
        
        // Обновляем цветовой пикер если введен валидный HEX
        if (/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(value)) {
            if (customColorInput) {
                customColorInput.value = value.length === 4 ? 
                    '#' + value[1] + value[1] + value[2] + value[2] + value[3] + value[3] : value;
            }
        }
    });
    
    customColorHex.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            applyCustomColor();
        }
    });
}

/**
 * Инициализация обработчиков событий
 */
function initEventListeners() {
    // Обработчик для кастомного цвета
    if (customColorInput) {
        customColorInput.addEventListener('input', function() {
            if (customColorHex) {
                customColorHex.value = this.value;
            }
        });
    }
    
    // Обработчик для кнопки применения цвета
    if (applyColorBtn) {
        applyColorBtn.addEventListener('click', applyCustomColor);
    }
    
    // Обработчик скролла
    window.addEventListener('scroll', handleScroll);
    
    // Глобальная обработка ошибок
    window.addEventListener('error', function(event) {
        console.error('Глобальная ошибка:', event.error);
        showNotification('Произошла ошибка приложения', 'error');
    });
    
    // Обработка события загрузки страницы
    window.addEventListener('load', function() {
        setTimeout(() => {
            checkForQRResult();
        }, 500);
    });
}

/**
 * Обработчик скролла
 */
function handleScroll() {
    // Можно добавить логику для фиксированных элементов при необходимости
}

/**
 * Проверяем, есть ли результат QR-кода на странице
 */
function checkForQRResult() {
    const qrResult = document.getElementById('qrResult');
    const urlHash = window.location.hash;
    
    if (qrResult && (urlHash === '#qrResult' || formSubmitted || shouldScrollToResult())) {
        setTimeout(() => {
            scrollToQRResult();
        }, 300);
        
        // Сохраняем URL QR-кода
        const qrImage = document.querySelector('.qr-image');
        if (qrImage && qrImage.src) {
            currentQRDataUrl = qrImage.src;
        }
    }
}

/**
 * Проверяем, нужно ли прокручивать к результату
 */
function shouldScrollToResult() {
    const urlParams = new URLSearchParams(window.location.search);
    const hasGeneratedQR = urlParams.has('generated') || document.querySelector('.qr-image');
    const formData = dataInput ? dataInput.value : '';
    
    return hasGeneratedQR || (formData && formData.trim().length > 0);
}

/**
 * Прокрутка к результату QR-кода
 */
function scrollToQRResult() {
    const qrResult = document.getElementById('qrResult');
    
    if (!qrResult) {
        console.log('Результат QR-кода не найден');
        return;
    }
    
    console.log('Прокрутка к результату QR-кода...');
    
    window.history.replaceState(null, null, '#qrResult');
    
    qrResult.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });
    
    qrResult.style.transition = 'box-shadow 0.5s ease';
    qrResult.style.boxShadow = '0 0 30px rgba(108, 99, 255, 0.5)';
    
    setTimeout(() => {
        qrResult.style.boxShadow = '';
    }, 2000);
    
    if (formSubmitted) {
        setTimeout(() => {
            showNotification('QR-код успешно сгенерирован!', 'success');
        }, 500);
        formSubmitted = false;
    }
}

/**
 * Инициализация кнопок выбора размера
 */
function initSizeButtons() {
    const sizeButtons = document.querySelectorAll('.size-btn');
    
    sizeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            if (!radio) return;
            
            sizeButtons.forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            radio.checked = true;
            
            console.log('Выбран размер:', radio.value);
            updateCharCounter();
        });
    });
}

/**
 * Инициализация валидации формы
 */
function initFormValidation() {
    const form = document.getElementById('qrForm');
    const generateBtn = document.getElementById('generateBtn');
    
    if (!form || !dataInput || !generateBtn) return;
    
    form.addEventListener('submit', function(event) {
        formSubmitted = true;
        
        // Показываем индикатор загрузки
        const loadingSpinner = document.getElementById('loadingSpinner');
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i> Генерация...';
        }
        
        setTimeout(() => {
            const qrResult = document.getElementById('qrResult');
            if (qrResult) {
                setTimeout(() => {
                    scrollToQRResult();
                    
                    // Скрываем индикатор загрузки
                    if (loadingSpinner) {
                        loadingSpinner.style.display = 'none';
                        generateBtn.disabled = false;
                        generateBtn.innerHTML = '<i class="bi bi-lightning-charge-fill me-2"></i> Сгенерировать QR-код';
                    }
                    
                    // Сохраняем URL QR-кода после генерации
                    const qrImage = document.querySelector('.qr-image');
                    if (qrImage && qrImage.src) {
                        currentQRDataUrl = qrImage.src;
                    }
                }, 100);
            }
        }, 100);
    });
    
    dataInput.addEventListener('input', function() {
        const hasData = this.value.trim().length > 0;
        
        if (generateBtn) {
            generateBtn.disabled = !hasData;
            generateBtn.classList.toggle('btn-primary', hasData);
            generateBtn.classList.toggle('btn-secondary', !hasData);
        }
    });
}

/**
 * Инициализация счетчика символов
 */
function initCharCounter() {
    if (!dataInput || !charCountElement || !maxCharsInfoElement || !charProgressElement) {
        console.log('Элементы счетчика символов не найдены');
        return;
    }
    
    dataInput.addEventListener('input', updateCharCounter);
    
    document.querySelectorAll('.size-btn input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', updateCharCounter);
    });
    
    const errorSelect = document.getElementById('errorCorrectionSelect');
    if (errorSelect) {
        errorSelect.addEventListener('change', updateCharCounter);
    }
    
    updateCharCounter();
}

/**
 * Обновление счетчика символов
 */
function updateCharCounter() {
    if (!dataInput || !charCountElement || !maxCharsInfoElement || !charProgressElement) return;
    
    const text = dataInput.value;
    const charCount = text.length;
    
    charCountElement.textContent = charCount;
    
    const selectedSize = document.querySelector('.size-btn.selected');
    const errorSelect = document.getElementById('errorCorrectionSelect');
    const errorLevel = errorSelect ? errorSelect.value : 'M';
    
    let maxChars = 240;
    let limitText = '~240 символов';
    
    if (selectedSize) {
        const maxCharsData = selectedSize.getAttribute('data-max-chars');
        if (maxCharsData) {
            try {
                const limits = JSON.parse(maxCharsData);
                limitText = limits[errorLevel] || limits['M'] || '~240 символов';
                maxChars = parseInt(limitText.replace(/[^\d]/g, '')) || 240;
                
                maxCharsInfoElement.innerHTML = `<span class="max-chars-value">${limitText}</span>`;
            } catch (e) {
                console.error('Ошибка парсинга данных о лимитах:', e);
                maxCharsInfoElement.innerHTML = '<span class="max-chars-value">~240 символов</span>';
            }
        }
    }
    
    const percentage = Math.min((charCount / maxChars) * 100, 100);
    charProgressElement.style.width = percentage + '%';
    
    // Обновляем цвета индикатора
    updateProgressColors(percentage, charCount, maxChars);
    
    // Показываем предупреждение если превышен лимит
    if (charCount > maxChars) {
        showHint(`Превышен лимит символов! Максимум для выбранного размера: ${maxChars}. Рекомендуется выбрать больший размер или сократить текст.`);
    }
}

/**
 * Обновление цветов индикатора прогресса
 */
function updateProgressColors(percentage, charCount, maxChars) {
    charProgressElement.classList.remove('bg-success', 'bg-warning', 'bg-danger');
    charCountElement.classList.remove('text-danger', 'text-warning', 'text-success');
    maxCharsInfoElement.classList.remove('text-danger', 'text-warning', 'text-primary');
    
    if (percentage >= 90 || charCount > maxChars) {
        charProgressElement.classList.add('bg-danger');
        charCountElement.classList.add('text-danger');
        maxCharsInfoElement.classList.add('text-danger');
    } else if (percentage >= 70) {
        charProgressElement.classList.add('bg-warning');
        charCountElement.classList.add('text-warning');
        maxCharsInfoElement.classList.add('text-warning');
    } else {
        charProgressElement.classList.add('bg-success');
        charCountElement.classList.add('text-success');
        maxCharsInfoElement.classList.add('text-primary');
    }
    
    if (charCount > maxChars) {
        charCountElement.innerHTML = `<strong>${charCount} (превышен лимит!)</strong>`;
    }
}

/**
 * Показать подсказку
 */
function showHint(message) {
    let hintElement = document.getElementById('inputHint');
    
    if (!hintElement) {
        hintElement = document.createElement('div');
        hintElement.id = 'inputHint';
        hintElement.className = 'form-text text-warning mt-2';
        hintElement.style.display = 'none';
        
        if (dataInput && dataInput.parentNode) {
            dataInput.parentNode.appendChild(hintElement);
        }
    }
    
    hintElement.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i> ${message}`;
    hintElement.style.display = 'block';
    
    // Автоматическое скрытие через 5 секунд
    setTimeout(() => {
        hintElement.style.opacity = '0';
        hintElement.style.transition = 'opacity 0.3s ease';
        
        setTimeout(() => {
            hintElement.style.display = 'none';
            hintElement.style.opacity = '1';
        }, 300);
    }, 5000);
}

/**
 * Выбор цвета из палитры
 */
function selectColor(element, color) {
    console.log('Выбор цвета:', color);
    
    try {
        // Снимаем выделение со всех цветов
        document.querySelectorAll('.color-option').forEach(opt => {
            opt.classList.remove('selected');
            opt.innerHTML = '';
        });
        
        // Выделяем выбранный цвет
        if (element) {
            element.classList.add('selected');
            element.innerHTML = '<i class="bi bi-check"></i>';
        }
        
        // Обновляем скрытое поле
        if (colorInput) {
            colorInput.value = color;
        }
        
        // Обновляем кастомные поля
        if (customColorInput) {
            customColorInput.value = color;
        }
        
        if (customColorHex) {
            customColorHex.value = color;
        }
        
        showNotification(`Цвет применен: ${color}`, 'success');
        
    } catch (error) {
        console.error('Ошибка при выборе цвета:', error);
        showNotification('Ошибка при выборе цвета', 'error');
    }
}

/**
 * Применение кастомного цвета
 */
function applyCustomColor() {
    let selectedColor = '';
    
    // Получаем цвет из HEX поля или цветового пикера
    if (customColorHex && customColorHex.value.trim()) {
        selectedColor = customColorHex.value.trim();
        
        // Добавляем # если его нет
        if (!selectedColor.startsWith('#')) {
            selectedColor = '#' + selectedColor;
        }
        
        // Валидация HEX цвета
        const hexPattern = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
        if (!hexPattern.test(selectedColor)) {
            showNotification('Неверный формат HEX цвета. Используйте #RRGGBB или #RGB', 'error');
            return;
        }
        
        // Конвертируем 3-значный формат в 6-значный
        if (selectedColor.length === 4) {
            selectedColor = '#' + selectedColor[1] + selectedColor[1] + 
                           selectedColor[2] + selectedColor[2] + 
                           selectedColor[3] + selectedColor[3];
        }
    } else if (customColorInput) {
        selectedColor = customColorInput.value;
    } else {
        selectedColor = '#000000';
    }
    
    console.log('Применение кастомного цвета:', selectedColor);
    
    // Обновляем скрытое поле
    if (colorInput) {
        colorInput.value = selectedColor;
    }
    
    // Обновляем цветовой пикер
    if (customColorInput) {
        customColorInput.value = selectedColor;
    }
    
    // Обновляем HEX поле
    if (customColorHex) {
        customColorHex.value = selectedColor;
    }
    
    // Проверяем, есть ли этот цвет в палитре
    let colorFound = false;
    document.querySelectorAll('.color-option').forEach(opt => {
        const optionColor = opt.getAttribute('data-color');
        if (optionColor && optionColor.toLowerCase() === selectedColor.toLowerCase()) {
            selectColor(opt, selectedColor);
            colorFound = true;
        }
    });
    
    // Если цвет не найден в палитре, снимаем выделение со всех цветов
    if (!colorFound) {
        document.querySelectorAll('.color-option').forEach(opt => {
            opt.classList.remove('selected');
            opt.innerHTML = '';
        });
        
        showNotification(`Кастомный цвет применен: ${selectedColor}`, 'success');
    }
}

/**
 * Показать уведомление
 */
function showNotification(message, type = 'info') {
    console.log(`Уведомление [${type}]:`, message);
    
    // Удаляем старые уведомления
    const oldNotifications = document.querySelectorAll('.notification');
    oldNotifications.forEach(notification => {
        notification.remove();
    });
    
    // Создаем новое уведомление
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Выбираем иконку в зависимости от типа
    let icon = 'bi-info-circle';
    if (type === 'error') icon = 'bi-exclamation-triangle';
    if (type === 'success') icon = 'bi-check-circle';
    if (type === 'warning') icon = 'bi-exclamation-circle';
    
    notification.innerHTML = `
        <i class="bi ${icon} me-2"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Показываем уведомление
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Автоматическое скрытие через 3 секунды
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 3000);
}

/**
 * Копировать изображение QR-кода в буфер обмена
 */
async function copyQRImage() {
    if (!currentQRDataUrl) {
        showNotification('QR-код не найден', 'error');
        return;
    }
    
    try {
        // Преобразуем Data URL в Blob
        const response = await fetch(currentQRDataUrl);
        const blob = await response.blob();
        
        // Создаем ClipboardItem
        const item = new ClipboardItem({
            [blob.type]: blob
        });
        
        // Копируем в буфер обмена
        await navigator.clipboard.write([item]);
        
        showNotification('QR-код скопирован в буфер обмена!', 'success');
        
    } catch (error) {
        console.error('Ошибка копирования изображения:', error);
        
        // Fallback для старых браузеров
        try {
            copyQRImageFallback();
        } catch (fallbackError) {
            showNotification('Не удалось скопировать QR-код. Используйте "Скачать PNG"', 'error');
        }
    }
}

/**
 * Fallback метод копирования изображения
 */
function copyQRImageFallback() {
    if (!currentQRDataUrl) return;
    
    // Создаем временный элемент canvas
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const img = new Image();
    
    img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        
        // Пытаемся скопировать через canvas
        canvas.toBlob(function(blob) {
            const item = new ClipboardItem({
                [blob.type]: blob
            });
            
            navigator.clipboard.write([item]).then(() => {
                showNotification('QR-код скопирован в буфер обмена!', 'success');
            }).catch(err => {
                console.error('Fallback копирование не удалось:', err);
                showNotification('Не удалось скопировать QR-код', 'error');
            });
        });
    };
    
    img.src = currentQRDataUrl;
}

/**
 * Поделиться изображением QR-кода
 */
async function shareQRImage() {
    if (!currentQRDataUrl) {
        showNotification('QR-код не найден', 'error');
        return;
    }
    
    // Проверяем поддержку Web Share API Level 2 (для файлов)
    if (navigator.canShare && navigator.canShare({ files: [] })) {
        try {
            // Преобразуем Data URL в File
            const response = await fetch(currentQRDataUrl);
            const blob = await response.blob();
            const file = new File([blob], 'qr_code.png', { type: 'image/png' });
            
            const shareData = {
                title: 'Мой QR-код',
                text: 'Посмотрите мой QR-код!',
                files: [file]
            };
            
            if (navigator.canShare(shareData)) {
                await navigator.share(shareData);
                return;
            }
        } catch (error) {
            console.log('Web Share API для файлов не поддерживается:', error);
        }
    }
    
    // Fallback: открываем попап с вариантами поделиться
    createImageSharePopup();
}

/**
 * Создать попап для выбора способа поделиться изображением
 */
function createImageSharePopup() {
    if (!currentQRDataUrl) return;
    
    // Удаляем старый попап если есть
    const oldPopup = document.getElementById('sharePopup');
    if (oldPopup) {
        oldPopup.remove();
    }
    
    // Получаем текст для описания
    const originalData = document.getElementById('dataInput')?.value || 'Мой QR-код';
    const safeOriginalData = originalData.replace(/'/g, "\\'");
    
    // Создаем попап
    const popup = document.createElement('div');
    popup.id = 'sharePopup';
    popup.className = 'share-popup';
    popup.innerHTML = `
        <div class="share-popup-content" id="sharePopupContent">
            <div class="share-popup-header">
                <h5><i class="bi bi-share me-2"></i> Поделиться QR-кодом</h5>
                <button type="button" class="btn-close btn-close-white" id="closeSharePopupBtn"></button>
            </div>
            <div class="share-popup-body">
                <div class="qr-preview mb-3 text-center">
                    <p class="small text-muted mb-2">Предпросмотр QR-кода:</p>
                    <img src="${currentQRDataUrl}" alt="QR код" class="img-thumbnail" style="max-width: 150px;">
                </div>
                <p class="small text-muted mb-3">
                    Выберите способ для отправки изображения QR-кода:
                </p>
                <div class="share-options">
                    <button class="share-option" data-platform="whatsapp">
                        <i class="bi bi-whatsapp"></i>
                        <span>WhatsApp</span>
                    </button>
                    <button class="share-option" data-platform="telegram">
                        <i class="bi bi-telegram"></i>
                        <span>Telegram</span>
                    </button>
                    <button class="share-option" data-platform="email">
                        <i class="bi bi-envelope"></i>
                        <span>Email</span>
                    </button>
                    <button class="share-option" data-platform="download">
                        <i class="bi bi-download"></i>
                        <span>Скачать</span>
                    </button>
                </div>
                <div class="share-note mt-3">
                    <p class="small text-muted">
                        <i class="bi bi-info-circle me-1"></i>
                        При выборе WhatsApp, Telegram или Email изображение QR-кода будет отправлено как файл
                    </p>
                </div>
            </div>
            <div class="share-popup-footer">
                <button type="button" class="btn btn-sm btn-outline-secondary" id="closeSharePopupBtn2">
                    Закрыть
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(popup);
    
    // Добавляем обработчики событий после создания DOM
    setTimeout(() => {
        initImageSharePopupEvents(safeOriginalData);
    }, 10);
    
    // Показываем попап с анимацией
    setTimeout(() => {
        popup.classList.add('show');
    }, 50);
}

/**
 * Инициализация обработчиков событий для попапа
 */
function initImageSharePopupEvents(originalData) {
    // Кнопки закрытия
    document.getElementById('closeSharePopupBtn').addEventListener('click', closeSharePopup);
    document.getElementById('closeSharePopupBtn2').addEventListener('click', closeSharePopup);
    
    // Обработчики для кнопок соцсетей
    document.querySelectorAll('.share-option').forEach(btn => {
        btn.addEventListener('click', function() {
            const platform = this.getAttribute('data-platform');
            shareImageViaPlatform(platform, originalData);
        });
    });
    
    // Закрытие при клике вне попапа
    document.getElementById('sharePopup').addEventListener('click', function(event) {
        if (event.target === this) {
            closeSharePopup();
        }
    });
}


/**
 * Отправить изображение по email
 */
async function shareImageViaEmail(blob, text) {
    // Создаем объект FormData для отправки
    const formData = new FormData();
    formData.append('qr_code', blob, 'qr_code.png');
    
    // Для email используем mailto: с текстом
    // Note: Прямая отправка файлов через mailto: не поддерживается
    // Поэтому отправляем только текст со ссылкой на изображение
    const subject = encodeURIComponent('Мой QR-код');
    const body = encodeURIComponent(`${text}\n\nQR код доступен по ссылке: ${currentQRDataUrl}`);
    const mailtoUrl = `mailto:?subject=${subject}&body=${body}`;
    
    window.location.href = mailtoUrl;
}

/**
 * Скачать изображение QR-кода
 */
function downloadQRImage() {
    if (!currentQRDataUrl) return;
    
    const link = document.createElement('a');
    link.href = currentQRDataUrl;
    link.download = 'qr_code.png';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('QR-код скачан!', 'success');
}

/**
 * Закрыть попап для поделиться
 */
function closeSharePopup() {
    const popup = document.getElementById('sharePopup');
    if (popup) {
        popup.classList.remove('show');
        setTimeout(() => {
            popup.remove();
        }, 300);
    }
}

/**
 * Закрытие попапа при нажатии Escape
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSharePopup();
    }
});

function makeAnotherQR() {
    // Сбрасываем URL
    window.history.replaceState(null, null, window.location.pathname);
    
    // Закрываем попап если открыт
    closeSharePopup();
    
    // Сбрасываем текущий QR-код
    currentQRDataUrl = null;
    
    // Прокручиваем к форме
    const formElement = document.getElementById('generatorForm');
    if (formElement) {
        formElement.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
    
    // Сбрасываем поля формы
    if (dataInput) {
        dataInput.value = '';
        dataInput.focus();
    }
    
    // Сбрасываем цвет на черный
    const blackColor = document.querySelector('.color-option[data-color="#000000"]');
    if (blackColor) {
        selectColor(blackColor, '#000000');
    }
    
    // Сбрасываем размер на средний
    const mediumSize = document.querySelector('.size-btn[data-size-id="m"]');
    if (mediumSize) {
        mediumSize.click();
    }
    
    // Сбрасываем уровень коррекции на M
    const errorSelect = document.getElementById('errorCorrectionSelect');
    if (errorSelect) {
        errorSelect.value = 'M';
    }
    
    // Обновляем счетчик символов
    updateCharCounter();
    
    showNotification('Форма сброшена. Введите новые данные', 'info');
}

/**
 * Прокрутка к форме
 */
function scrollToForm() {
    const formElement = document.getElementById('generatorForm');
    if (formElement) {
        formElement.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
        
        formElement.style.transition = 'box-shadow 0.5s ease';
        formElement.style.boxShadow = '0 0 30px rgba(108, 99, 255, 0.5)';
        
        setTimeout(() => {
            formElement.style.boxShadow = '';
        }, 2000);
    }
}

// Экспорт функций для глобального использования
window.scrollToForm = scrollToForm;
window.scrollToQRResult = scrollToQRResult;
window.selectColor = selectColor;
window.applyCustomColor = applyCustomColor;
window.shareQR = shareQRImage; // Изменено на shareQRImage
window.copyToClipboard = copyQRImage; // Изменено на copyQRImage
window.makeAnotherQR = makeAnotherQR;
window.updateCharCounter = updateCharCounter;
window.showNotification = showNotification;
window.closeSharePopup = closeSharePopup;