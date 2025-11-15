import requests
# ... سایر import ها ...

# تابع send_otp_request که قبلاً نوشتیم، در این فایل قرار دارد
def send_otp_request(mobile_number: str, proxy_url: str = "http://127.0.0.1:10808") -> dict:
    # ... پیاده سازی کامل تابع ...
    url = "https://api.khakpourgold.com/auth/send-otp"
    payload = {"mobile": mobile_number}
    headers = {"Content-Type": "application/json"}
    proxies = {"http": proxy_url, "https": proxy_url}

    try:
        response = requests.post(url, headers=headers, json=payload, proxies=proxies, verify=False, timeout=10)
        
        # در اینجا منطق را کمی ساده‌تر می‌کنیم تا فقط برای ویو کاربرد داشته باشد:
        if response.status_code == 204:
            return {'success': True, 'status_code': 204}
        else:
            try:
                error_data = response.json()
            except requests.exceptions.JSONDecodeError:
                error_data = {"message": response.text}
            
            return {'success': False, 'status_code': response.status_code, 'data': error_data}

    except requests.exceptions.RequestException as e:
        return {'success': False, 'status_code': 503, 'data': str(e)}










def get_token_request(mobile_number: str, otp_code: str, proxy_url: str = "http://127.0.0.1:10808") -> dict:
    """
    ارسال کد OTP و شماره موبایل به API برای دریافت توکن احراز هویت (کوکی).

    :param mobile_number: شماره موبایل.
    :param otp_code: کد OTP.
    :return: dict حاوی {'token': توکن کامل} یا {'error': پیام خطا}.
    """
    url = "https://api.khakpourgold.com/auth/token"
    payload = {"code": otp_code, "mobile": mobile_number}
    headers = {"Content-Type": "application/json"}
    proxies = {"http": proxy_url, "https": proxy_url}

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            proxies=proxies,
            verify=False,
            timeout=15
        )
        
        http_status = response.status_code
        
        # در صورت موفقیت (HTTP 204)
        if http_status == 204:
            access_token_cookie = response.cookies.get('access_token_web')
            if access_token_cookie:
                # 💡 برگشت توکن با کلید 'token' مطابق نیاز ویو
                return {'token': access_token_cookie, 'status_code': 204, 'headers': dict(response.headers)}
            
            return {'error': 'Authentication successful but no access token cookie received.', 'status_code': 204}
        
        # در صورت خطا (مثلاً 400 - کد اشتباه)
        else:
            try:
                error_data = response.json()
            except requests.exceptions.JSONDecodeError:
                error_data = {"message": response.text}
            
            # 💡 برگشت پیام خطا با کلید 'error'
            return {'error': error_data, 'status_code': http_status}

    except requests.exceptions.RequestException as e:
        return {'error': f"Request failed: {str(e)}", 'status_code': 503}