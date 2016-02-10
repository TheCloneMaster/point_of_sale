# -*- coding: utf-8 -*-

from openerp import models, fields
from openerp import tools

class so_pos_order_report(models.Model):
     _name = "report.so.pos.order"
     _description = "Consolidated Sale and Point of Sale Orders Statistics"
     _auto = False
     _order = 'date desc'

     date = fields.Date(string='Date Order', readonly=True)
     partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
     product_id = fields.Many2one('product.product', string='Product', readonly=True)
     product_uom = fields.Many2one('product.uom', string='Unit of Measure', readonly=True)
     categ_id = fields.Many2one('product.category',string='Product Category', readonly=True)
     state = fields.Selection([('draft', 'New'), ('paid', 'Closed'), ('done', 'Synchronized'), ('invoiced', 'Invoiced'), ('cancel', 'Cancelled'), ('manual', 'Sale to Invoice')],
     string='Status')
     user_id = fields.Many2one('res.users', string='Salesperson', readonly=True)
     price_total = fields.Float(string='Total Price', readonly=True)
     total_discount = fields.Float(string='Total Discount', readonly=True)
     price_total_crc = fields.Float(string='Total Price CRC', readonly=True)
     total_discount_crc = fields.Float(string='Total Discount CRC', readonly=True)
     company_id = fields.Many2one('res.company', string='Company', readonly=True)
     nbr = fields.Integer(string='# of Lines', readonly=True)
     product_qty = fields.Integer(string='Product Quantity', readonly=True)
     delay_validation = fields.Integer(string='Delay Validation')
     type = fields.Selection([('sale','Sale'), ('pos','Pos')], string="Sales Channel")
     picked = fields.Integer(string='Picked', readonly=True)
     warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
     picking_id = fields.Many2one('stock.picking', string='Picking', readonly=True)
     cif_price = fields.Float(string='CIF Price', readonly=True)
     stock_qty = fields.Float(string='Stock Qty', readonly=True)
     total_cost_price = fields.Float(string='Total Cost Price', readonly=True)
     total_cost_price_crc = fields.Float(string='Total Cost Price CRC', readonly=True)
     order_name= fields.Char(string='Order Name', readonly=True)

     def init(self, cr):
         tools.drop_view_if_exists(cr, 'report_so_pos_order')
         cr.execute(""" CREATE OR REPLACE VIEW report_so_pos_order AS (
SELECT
             -min(pos_line.id) AS id,
             count(*) AS nbr,
             to_date(to_char(pos_order.date_order - interval '1 hour','YYYY-MM-DD'),'YYYY-MM-DD') AS date,
             sum(pos_line.qty * uom.factor) AS product_qty,
             sum(pos_line.price_subtotal) AS price_total,
             sum((pos_line.qty * pos_line.price_unit) * (pos_line.discount / 100)) AS total_discount,
             sum(pos_line.price_subtotal*currency.rate) AS price_total_crc,
             sum((pos_line.qty * pos_line.price_unit*currency.rate) * (pos_line.discount / 100)) AS total_discount_crc,
             pos_order.partner_id AS partner_id,
             pos_order.state AS state,
             pos_order.user_id AS user_id,
             count(pos_order.picking_id) AS picked,
             pos_order.company_id AS company_id,
             pos_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             picking_move.warehouse_id AS warehouse_id,
             'pos' AS type,
             picking_move.picking_id AS picking_id,
             picking_move.price_unit AS cif_price,
             picking_move.product_qty AS stock_qty,
             picking_move.price_unit * picking_move.product_qty AS total_cost_price,
             picking_move.price_unit * picking_move.product_qty * currency.rate AS total_cost_price_crc,
             pos_order.name AS order_name
             FROM ( select company_id,
                           order_id,
                           product_id,
                           min(id) id,
                           max(price_unit) price_unit,
                           max(discount) discount,
                           sum(price_subtotal) price_subtotal,
                           sum(price_subtotal_incl) price_subtotal_incl,
                           sum(qty) qty
                    from pos_order_line
                    group by company_id,
                           order_id,
                           product_id
             ) AS pos_line
             LEFT JOIN pos_order pos_order ON (pos_order.id=pos_line.order_id)
             LEFT JOIN product_product product ON (pos_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=template.uom_id)

             LEFT JOIN ( select min(picking.name),
                                picking.origin,
                                move.partner_id,
                                move.company_id,
                                min(move.picking_id) as picking_id,
                                move.product_id,
                                warehouse_id,
                                max(move.price_unit) price_unit,
                                sum(move.product_qty) product_qty
                         from stock_picking picking, stock_move move
                         where picking.id = move.picking_id
                         group by picking.origin,
                                move.partner_id,
                                move.company_id,
                                move.product_id,
                                warehouse_id
             ) as picking_move ON (pos_order.name = picking_move.origin and pos_line.product_id=picking_move.product_id )
	     , res_currency_rate currency
             WHERE  pos_order.state in ('done','paid')
             and currency_id = 40 and currency.name <= pos_order.date_order
             and currency.id in (select id FROM res_currency_rate
                                 WHERE currency_id = 40
                                 AND name <= pos_order.date_order
                                 ORDER BY name desc LIMIT 1)
             GROUP BY
             pos_order.date_order, pos_order.partner_id,template.categ_id,pos_order.state,template.uom_id,
             pos_order.user_id,pos_order.company_id,pos_line.product_id,pos_order.create_date,pos_order.picking_id,
             picking_move.warehouse_id, picking_move.picking_id, cif_price, stock_qty, total_cost_price, order_name
             , currency.rate

             HAVING
             sum(pos_line.qty * uom.factor) != 0
union all
SELECT
             min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             sum(invoice_line.price_subtotal) AS price_total,
             sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             sum(invoice_line.price_subtotal*currency.rate) AS price_total_crc,
             sum((invoice_line.quantity * invoice_line.price_unit*currency.rate) * (invoice_line.discount / 100)) AS total_discount_crc,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'sale' AS type,
             min(picking_move.picking_id) AS picking_id,
             max(picking_move.price_unit) AS cif_price,
             sum(picking_move.product_qty * (case when invoice_line.quantity > 0 then 1 else -1 end) ) AS stock_qty,
             sum(picking_move.price_unit * picking_move.product_qty * (case when invoice_line.quantity > 0 then 1 else -1 end)) AS total_cost_price,
             sum(picking_move.price_unit * picking_move.product_qty*currency.rate * (case when invoice_line.quantity > 0 then 1 else -1 end)) AS total_cost_price_crc,
             invoice.number || ' (' || invoice.origin || ')' AS order_name
             FROM (select min(il.id) id,
                          company_id,
                          invoice_id,
                          product_id,
                          partner_id,
                          uos_id,
                          max(price_unit) price_unit,
                          sum(quantity) quantity,
                          sum(price_subtotal) price_subtotal,
                          max(discount) discount
                   from account_invoice_line il
                   group by company_id,
                          invoice_id,
                          product_id,
                          partner_id, uos_id) AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id)
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)
             LEFT JOIN ( select picking.group_id,
                                min(picking.name) as name,
                                coalesce(move.origin, picking.origin) origin,
                                move.partner_id,
                                move.company_id,
                                min(move.picking_id) as picking_id,
                                move.product_id,
                                max(move.price_unit) price_unit,
                                sum(move.product_qty) product_qty
                         from stock_picking picking, stock_move move
                         where picking.id = move.picking_id
                         group by picking.group_id, 3,
                                move.partner_id,
                                move.company_id,
                                move.product_id
             ) as picking_move ON ( ( (sale_order.procurement_group_id = picking_move.group_id and picking_move.name like 'WH/OUT/%') or
                                    (invoice.origin = picking_move.origin) )
                                   and invoice_line.product_id = picking_move.product_id)
	     , res_currency_rate currency
             where invoice.type in ('out_invoice') and
                   invoice.state in ('open','paid')
             and currency.currency_id = 40 and currency.name <= invoice.date_invoice
             and currency.id in (select id FROM res_currency_rate
                                 WHERE currency_id = 40
                                 AND name <= invoice.date_invoice
                                 ORDER BY name desc LIMIT 1)
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id, picking_move.picking_id, order_name
             , currency.rate
union all
             SELECT
             min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             sum(invoice_line.price_subtotal) AS price_total,
             sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             sum(invoice_line.price_subtotal*currency.rate) AS price_total_crc,
             sum((invoice_line.quantity * invoice_line.price_unit*currency.rate) * (invoice_line.discount / 100)) AS total_discount_crc,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'sale' AS type,
             min(picking_move.picking_id) AS picking_id,
             max(picking_move.price_unit) AS cif_price,
             sum(picking_move.product_qty) AS stock_qty,
             sum(picking_move.price_unit * picking_move.product_qty) AS total_cost_price,
             sum(picking_move.price_unit * picking_move.product_qty*currency.rate) AS total_cost_price_crc,
             invoice.number || ' (' || invoice.origin || ')' AS order_name
             FROM (select min(il.id) id,
                          company_id,
                          invoice_id,
                          product_id,
                          partner_id,
                          uos_id,
                          max(price_unit) price_unit,
                          sum(quantity) quantity,
                          sum(price_subtotal) price_subtotal,
                          max(discount) discount
                   from account_invoice_line il
                   group by company_id,
                          invoice_id,
                          product_id,
                          partner_id, uos_id) AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id)
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)
             LEFT JOIN ( select picking.group_id,
                                min(picking.name) as name,
                                coalesce(move.origin, picking.origin) origin,
                                move.partner_id,
                                move.company_id,
                                min(move.picking_id) as picking_id,
                                move.product_id,
                                max(move.price_unit) price_unit,
                                sum(move.product_qty) product_qty
                         from stock_picking picking, stock_move move
                         where picking.id = move.picking_id
                         group by picking.group_id, 3,
                                move.partner_id,
                                move.company_id,
                                move.product_id
             ) as picking_move ON ( ( (sale_order.procurement_group_id = picking_move.group_id and picking_move.name like 'WH/OUT/%') or
                                    (invoice.origin = picking_move.origin) )
                                   and invoice_line.product_id = picking_move.product_id)
	     , res_currency_rate currency
             where invoice.type in ('out_refund') and
                   invoice.state in ('open','paid')
             and currency.currency_id = 40 and currency.name <= invoice.date_invoice
             and currency.id in (select id FROM res_currency_rate
                                 WHERE currency_id = 40
                                 AND name <= invoice.date_invoice
                                 ORDER BY name desc LIMIT 1)
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id, picking_move.picking_id, order_name
             , currency.rate
order by type, picking_id, order_name, product_id
          )""")

     """  versión casi original, total 149  !!!!!!!!!











             -min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             -sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             -sum(invoice_line.price_subtotal) AS price_total,
             -sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'refund' AS type,
             picking_move.picking_id AS picking_id,
             picking_move.price_unit AS cif_price,
             picking_move.product_qty AS stock_qty,
             picking_move.price_unit * picking_move.product_qty AS total_cost_price,
             invoice.origin AS order_name
             FROM (select min(il.id) id,
                          company_id,
                          invoice_id,
                          product_id,
                          partner_id,
                          uos_id,
                          max(price_unit) price_unit,
                          sum(quantity) quantity,
                          sum(price_subtotal) price_subtotal,
                          max(discount) discount
                   from account_invoice_line il
                   group by company_id,
                          invoice_id,
                          product_id,
                          partner_id, uos_id) AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id)
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)

             LEFT JOIN ( select picking.group_id,
                                min(picking.name) as name,
                                move.origin,
                                move.partner_id,
                                move.company_id,
                                min(move.picking_id) as picking_id,
                                move.product_id,
                                max(move.price_unit) price_unit,
                                sum(move.product_qty) product_qty
                         from stock_picking picking, stock_move move
                         where picking.id = move.picking_id
                         group by picking.group_id, move.origin,
                                move.partner_id,
                                move.company_id,
                                move.product_id
             ) as picking_move ON (sale_order.procurement_group_id = picking_move.group_id and invoice.origin=picking_move.name)

             where invoice.type = 'out_refund' and
                   invoice.state in ('open','paid') and
                   picking_move.product_id = invoice_line.product_id
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id, picking_move.picking_id, cif_price, stock_qty, total_cost_price, order_name









             SELECT
             -min(pos_line.id) AS id,
             count(*) AS nbr,
             pos_order.date_order AS date,
             sum(pos_line.qty * uom.factor) AS product_qty,
             sum(pos_line.qty * pos_line.price_unit) AS price_total,
             sum((pos_line.qty * pos_line.price_unit) * (pos_line.discount / 100)) AS total_discount,
             sum(cast(to_char(date_trunc('day',pos_order.date_order) - date_trunc('day',pos_order.create_date),'DD') AS int)) AS delay_validation,
             pos_order.partner_id AS partner_id,
             pos_order.state AS state,
             pos_order.user_id AS user_id,
             count(pos_order.picking_id) AS picked,
             pos_order.company_id AS company_id,
             pos_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             move.warehouse_id AS warehouse_id,
             'pos' AS type

             FROM pos_order_line AS pos_line
             LEFT JOIN pos_order pos_order ON (pos_order.id=pos_line.order_id)
             LEFT JOIN product_product product ON (pos_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=template.uom_id)
             LEFT JOIN stock_picking picking ON (pos_order.partner_id = picking.partner_id and pos_order.name = picking.origin)
             LEFT JOIN stock_move move ON (picking.id = move.picking_id and move.product_id = pos_line.product_id)
             where pos_order.date_order >= '2015-02-01'
             GROUP BY
             pos_order.date_order, pos_order.partner_id,template.categ_id,pos_order.state,template.uom_id,
             pos_order.user_id,pos_order.company_id,pos_line.product_id,pos_order.create_date,pos_order.picking_id, move.warehouse_id
             HAVING
             sum(pos_line.qty * uom.factor) != 0
             UNION ALL
             SELECT
             min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             sum(invoice_line.quantity * invoice_line.price_unit) AS price_total,
             sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             extract(epoch from avg(date_trunc('day',invoice.date_invoice)-date_trunc('day',invoice.create_date)))/(24*60*60)::decimal(16,2) AS delay_validation,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'sale' AS type

             FROM account_invoice_line AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id)
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)
             where invoice.date_invoice >= '2015-02-01'
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id
             order by type, order_name, product_id
     """





     """
                  SELECT
             -min(pos_line.id) AS id,
             count(*) AS nbr,
             pos_order.date_order AS date,
             sum(pos_line.qty * uom.factor) AS product_qty,
             sum(pos_line.qty * pos_line.price_unit) AS price_total,
             sum((pos_line.qty * pos_line.price_unit) * (pos_line.discount / 100)) AS total_discount,
             sum(cast(to_char(date_trunc('day',pos_order.date_order) - date_trunc('day',pos_order.create_date),'DD') AS int)) AS delay_validation,
             pos_order.partner_id AS partner_id,
             pos_order.state AS state,
             pos_order.user_id AS user_id,
             count(pos_order.picking_id) AS picked,
             pos_order.company_id AS company_id,
             pos_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             move.warehouse_id AS warehouse_id,
             'pos' AS type,
             picking.id AS picking_id,
             move.price_unit AS cif_price,
             move.product_qty AS stock_qty,
             move.price_unit * move.product_qty AS total_cost_price,
             pos_order.name AS order_name

             FROM pos_order_line AS pos_line
             LEFT JOIN pos_order pos_order ON (pos_order.id=pos_line.order_id and pos_order.state in ('done','paid'))
             LEFT JOIN product_product product ON (pos_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=template.uom_id)
             LEFT JOIN stock_picking picking ON (pos_order.name = picking.origin)
             LEFT JOIN stock_move move ON (picking.id = move.picking_id and move.product_id = pos_line.product_id)
             where pos_order.date_order >= '2015-02-01'
             GROUP BY
             pos_order.date_order, pos_order.partner_id,template.categ_id,pos_order.state,template.uom_id,
             pos_order.user_id,pos_order.company_id,pos_line.product_id,pos_order.create_date,pos_order.picking_id,
             move.warehouse_id, picking.id, cif_price, stock_qty, total_cost_price, order_name
             HAVING
             sum(pos_line.qty * uom.factor) != 0
             SELECT
             min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             sum(invoice_line.quantity * invoice_line.price_unit) AS price_total,
             sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             extract(epoch from avg(date_trunc('day',invoice.date_invoice)-date_trunc('day',invoice.create_date)))/(24*60*60)::decimal(16,2) AS delay_validation,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'sale' AS type,
             move.picking_id AS picking_id,
             move.price_unit AS cif_price,
             move.product_qty AS stock_qty,
             move.price_unit * move.product_qty AS total_cost_price,
             invoice.origin AS order_name
,sale_invoice.invoice_id
,sale_invoice.order_id
             FROM account_invoice_line AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id and
                                                   invoice.type in ('out_invoice') and
                                                   invoice.state in ('open','paid'))
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)
             LEFT JOIN stock_picking picking ON (sale_order.procurement_group_id = picking.group_id and picking.name like 'WH/OUT/%')
             LEFT JOIN stock_move move ON (picking.id = move.picking_id)
             where invoice.date_invoice >= '2015-02-01' and move.product_id = invoice_line.product_id and sale_order.id = 319
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id, move.picking_id, cif_price, stock_qty, total_cost_price, order_name
,sale_invoice.invoice_id   ,sale_invoice.order_id

union all
             SELECT
             min(invoice_line.id) AS id,
             count(*) AS nbr,
             invoice.date_invoice AS date,
             sum(invoice_line.quantity / uom.factor * template_uom.factor) AS product_qty,
             sum(invoice_line.quantity * invoice_line.price_unit) AS price_total,
             sum((invoice_line.quantity * invoice_line.price_unit) * (invoice_line.discount / 100)) AS total_discount,
             extract(epoch from avg(date_trunc('day',invoice.date_invoice)-date_trunc('day',invoice.create_date)))/(24*60*60)::decimal(16,2) AS delay_validation,
             invoice.partner_id AS partner_id,
             invoice.state AS state,
             invoice.user_id AS user_id,
             sale_order.shipped::integer AS picked,
             invoice.company_id AS company_id,
             invoice_line.product_id AS product_id,
             template.uom_id AS product_uom,
             template.categ_id AS categ_id,
             sale_order.warehouse_id AS warehouse_id,
             'sale' AS type,
             move.picking_id AS picking_id,
             move.price_unit AS cif_price,
             move.product_qty AS stock_qty,
             move.price_unit * move.product_qty AS total_cost_price,
             invoice.origin||'@@' AS order_name
,sale_invoice.invoice_id
,sale_invoice.order_id
             FROM account_invoice_line AS invoice_line
             LEFT JOIN account_invoice invoice ON (invoice.id=invoice_line.invoice_id and
                                                   invoice.type in ('out_refund') and
                                                   invoice.state in ('open','paid'))
             LEFT JOIN product_product product ON (invoice_line.product_id=product.id)
             LEFT JOIN product_template template ON (product.product_tmpl_id=template.id)
             LEFT JOIN product_uom uom ON (uom.id=invoice_line.uos_id)
             LEFT JOIN product_uom template_uom ON (template_uom.id=template.uom_id)
             LEFT JOIN sale_order_invoice_rel sale_invoice ON (sale_invoice.invoice_id=invoice.id)
             LEFT JOIN sale_order sale_order ON (sale_order.id=sale_invoice.order_id)

             LEFT JOIN stock_picking picking ON (sale_order.procurement_group_id = picking.group_id and picking.name = invoice.origin)
             LEFT JOIN stock_move move ON (picking.id = move.picking_id)
             where invoice.date_invoice >= '2015-02-01' and move.product_id = invoice_line.product_id and sale_order.id = 319
             GROUP BY
             invoice.date_invoice,invoice.partner_id,template.categ_id,invoice.state,template.uom_id,
             invoice.user_id,invoice.company_id,invoice_line.product_id,sale_order.shipped,sale_order.warehouse_id, move.picking_id, cif_price, stock_qty, total_cost_price, order_name
,sale_invoice.invoice_id   ,sale_invoice.order_id

order by type, picking_id, order_name, product_id

     """
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
