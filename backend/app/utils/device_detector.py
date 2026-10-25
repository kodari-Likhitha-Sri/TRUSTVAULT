import re
from flask import request

def get_client_ip(req=None):
    """Extract real client IP address considering proxy headers."""
    r = req or (request if request else None)
    if not r:
        return '127.0.0.1'
    
    # Check X-Forwarded-For header
    x_forwarded_for = r.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # X-Forwarded-For may contain multiple IPs: client, proxy1, proxy2
        return x_forwarded_for.split(',')[0].strip()
    
    # Check X-Real-IP
    x_real_ip = r.headers.get('X-Real-IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    return r.remote_addr or '127.0.0.1'

def get_device_info(req=None):
    """Extract device type and operating system from User-Agent string."""
    r = req or (request if request else None)
    if not r:
        return 'Desktop', 'Unknown Browser'
    
    ua = r.headers.get('User-Agent', '')
    if not ua:
        return 'Unknown Device', 'Unknown Browser'
    
    # Detect Device / OS
    device = 'Desktop'
    if 'Windows' in ua:
        device = 'Windows PC'
    elif 'iPhone' in ua:
        device = 'iPhone'
    elif 'iPad' in ua:
        device = 'iPad'
    elif 'Android' in ua:
        device = 'Android Device'
    elif 'Macintosh' in ua or 'Mac OS X' in ua:
        device = 'Mac Desktop'
    elif 'Linux' in ua:
        device = 'Linux PC'
    
    # Detect Browser
    browser = 'Browser'
    if 'Edg/' in ua or 'Edge/' in ua:
        browser = 'Microsoft Edge'
    elif 'Chrome/' in ua and 'Safari/' in ua:
        browser = 'Google Chrome'
    elif 'Firefox/' in ua:
        browser = 'Mozilla Firefox'
    elif 'Safari/' in ua and 'Chrome/' not in ua:
        browser = 'Apple Safari'
    elif 'Opera/' in ua or 'OPR/' in ua:
        browser = 'Opera'
    
    return device, browser
