from openerp import fields, models, api, _
from openerp import tools
from datetime import datetime
import time

class report_sales_dmy_custom(models.Model):
    _name = "report.sales.dmy.custom"
    _auto = False
    
    date_order = fields.Datetime('Date', readonly=True)
    daily = fields.Float('Daily Sales', digits=(16,2), readonly=True,
                                   help="Total amount of daily sales (sales on a date).")
    weekly = fields.Float('Weekly Sales', digits=(16,2), readonly=True,
                                   help="Total amount of weekly sales (Sunday to current day on the week).")
    monthly = fields.Float('Monthly Sales', digits=(16,2), readonly=True,
                                   help="Total amount of monthly sales (From 1st of the month to current date).")
    yearly = fields.Float('Yearly Sales', digits=(16,2), readonly=True,
                                   help="Total amount of yearly sales (From day one to current date of the financial).")

    def _weekly_sales_amount_en_dt(self):
        current_dt = datetime.now().date().strftime("%d/%b/%Y")
        day, mon, yr= current_dt.split("/")
        st_day = yr+" "+day+" "+mon
        from_dt = time.strptime(st_day, '%Y %d %b')
        start_dt = yr+" "+time.strftime("%U", from_dt )+" 0"
        end_dt = yr+" "+time.strftime("%U", from_dt )+" 6"
        week_start_dt = time.strptime(start_dt, '%Y %U %w')
        week_end_dt = time.strptime(end_dt, '%Y %U %w')
        w_st_dt = time.strftime("%Y-%m-%d", week_start_dt)
        w_en_dt = time.strftime("%Y-%m-%d", week_end_dt)
        return w_en_dt

    def _weekly_sales_amount_st_dt(self):
        current_dt = datetime.now().date().strftime("%d/%b/%Y")
        day, mon, yr= current_dt.split("/")
        st_day = yr+" "+day+" "+mon
        from_dt = time.strptime(st_day, '%Y %d %b')
        start_dt = yr+" "+time.strftime("%U", from_dt )+" 0"
        end_dt = yr+" "+time.strftime("%U", from_dt )+" 6"
        week_start_dt = time.strptime(start_dt, '%Y %U %w')
        week_end_dt = time.strptime(end_dt, '%Y %U %w')
        w_st_dt = time.strftime("%Y-%m-%d", week_start_dt)
        w_en_dt = time.strftime("%Y-%m-%d", week_end_dt)
        return w_st_dt
    

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'report_sales_dmy_custom')
        cr.execute(""" create or replace view report_sales_dmy_custom as (
                select
                   min(inv.id) as id,
                   (CASE WHEN  (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd') = CURRENT_DATE)
                    
                    THEN sum(inv.amount_total) ELSE 0
                     end )as daily,
                     
                   (CASE WHEN ((to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) >= '%s' and (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) <= '%s')
                    
                    THEN sum(inv.amount_total) ELSE 0
                     end )as weekly,
                (CASE WHEN  (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) >= (to_date(to_char(inv.date_order, 'YYYY-MM-01'),'YYYY-MM-01'))
                                            AND
                                            (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) <= inv.date_order
                    
                    THEN sum(inv.amount_total) ELSE 0
                     end )as monthly,
                     
                (CASE WHEN  (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) >= (to_date(to_char(CURRENT_DATE, 'YYYY-01-01'),'YYYY-01-01'))
                                                AND
                                                (to_date(to_char(inv.date_order, 'YYYY-MM-dd'),'YYYY-MM-dd')) <= CURRENT_DATE
                    
                    THEN sum(inv.amount_total) ELSE 0
                     end )as yearly,
                inv.date_order as date_order
            from
                sale_order as inv
            group by
                inv.id
        )"""% (self._weekly_sales_amount_st_dt(), self._weekly_sales_amount_en_dt()))
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: