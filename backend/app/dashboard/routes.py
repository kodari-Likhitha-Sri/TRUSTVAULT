from flask import Blueprint, render_template
from flask_login import current_user, login_required
from app.dashboard.service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    data = DashboardService.get_dashboard_metrics(current_user)
    return render_template('dashboard.html', **data)
