from flask import Blueprint, request, jsonify
from sqlalchemy import text
from ..utils.auth import require_auth, get_shop_context
from ..models.database import get_db

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/analytics/summary', methods=['GET'])
@require_auth
def analytics_summary():
    try:
        ctx = get_shop_context()
        days = int(request.args.get('days', 30))
        with get_db() as db:
            summary = {}

            # Totals by event type
            rows = db.execute(text('''
                select event_type,
                       count(*) as c
                from offer_events
                where shop_id = :sid
                  and timestamp >= (now() - (:days || ' days')::interval)
                  and event_type in ('offer_view','offer_select','purchase')
                group by event_type
            '''), { 'sid': ctx['shop_id'], 'days': days }).mappings().all()
            totals = { r['event_type']: int(r['c']) for r in rows }

            # By surface and type
            by_surface_rows = db.execute(text('''
                select coalesce(metadata->>'surface','unknown') as surface,
                       event_type,
                       count(*) as c
                from offer_events
                where shop_id = :sid
                  and timestamp >= (now() - (:days || ' days')::interval)
                  and event_type in ('offer_view','offer_select','purchase')
                group by 1, 2
            '''), { 'sid': ctx['shop_id'], 'days': days }).mappings().all()
            by_surface = {}
            for r in by_surface_rows:
                surf = r['surface'] or 'unknown'
                by_surface.setdefault(surf, {})[r['event_type']] = int(r['c'])

            # Time series per day
            ts_rows = db.execute(text('''
                select date_trunc('day', timestamp) as day,
                       event_type,
                       count(*) as c
                from offer_events
                where shop_id = :sid
                  and timestamp >= (now() - (:days || ' days')::interval)
                  and event_type in ('offer_view','offer_select','purchase')
                group by 1, 2
                order by 1 asc
            '''), { 'sid': ctx['shop_id'], 'days': days }).mappings().all()
            series = {}
            for r in ts_rows:
                day = r['day'].isoformat()
                series.setdefault(day, {})[r['event_type']] = int(r['c'])

            # Simple funnel conversions
            views = totals.get('offer_view', 0)
            selects = totals.get('offer_select', 0)
            purchases = totals.get('purchase', 0)
            conversion_select = (selects / views) if views else 0.0
            conversion_purchase = (purchases / views) if views else 0.0
            conversion_purchase_from_select = (purchases / selects) if selects else 0.0

            return jsonify({
                'days': days,
                'totals': {
                    'views': views,
                    'selects': selects,
                    'purchases': purchases,
                },
                'conversions': {
                    'select_over_view': conversion_select,
                    'purchase_over_view': conversion_purchase,
                    'purchase_over_select': conversion_purchase_from_select,
                },
                'by_surface': by_surface,
                'series': series,
            })
    except Exception as e:
        return jsonify({ 'error': str(e) }), 500


