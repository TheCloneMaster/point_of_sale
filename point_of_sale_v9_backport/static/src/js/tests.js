(function(){
    "use strict";

    window.pos_generate_random_orders = function(opts){
        opts = opts || {};
        opts.delay    = opts.delay || 1000;
        opts.min_order_size = opts.min_order_size || 1;
        opts.max_order_size = opts.max_order_size || 10;
        opts.prob_many_unit = opts.prob_many_unit || 0.1;
        opts.many_unit_max  = opts.many_unit_max  || 10;
        opts.prob_many_quant = opts.prob_many_quant || 0.8;
        opts.many_quant_max  = opts.many_quant_max  || 20;
        
        var module = openerp.point_of_sale;
        var pos    = window.posmodel;

        if (!pos){
            console.error("cannot generate random orders outside of the point of sale");
            return;
        }

        var products = [];
        for (var id in pos.db.product_by_id) {
            products.push(pos.db.product_by_id[id]);
        }

        var partners = [];
        for (var id in pos.db.partner_by_id) {
            partners.push(pos.db.partner_by_id[id]);
        }

        function proba(prob){
            return Math.random() <= prob;
        }

        function range(a,b){
            return a + Math.floor(Math.random()*(b-a));
        }

        function select(list){
            var i = Math.floor(Math.random()*(list.length - 0.00001));
            return list[i];
        }
        
        function generate(){

            var o = new module.Order({},{pos:pos});

            var os = range(opts.min_order_size,opts.max_order_size);

            while (os--) {
                var product = select(products);
                o.add_product(product);
                var ol = o.get_last_orderline();
                if (!ol.get_unit().rounding || ol.get_unit().rounding === 1) {
                    if (proba(opts.prob_many_unit)) {
                        ol.set_quantity(Math.ceil(range(2,opts.many_unit_max)));
                    }
                } else {
                    if (proba(opts.prob_many_quant)) {
                        ol.set_quantity(range(0,opts.many_quant_max));
                    }
                }
            }

            var total = o.get_total_with_tax();
            var min   = 1;
            var max   = Math.max(5,total*2);

            while (!o.is_paid()) {
                o.add_paymentline(select(pos.cashregisters));
                o.selected_paymentline.set_amount(range(min,max));
            }

            console.log('Pushing Order',o);
            
            pos.push_order(o);
        }

        function loop() {
            generate();
            if (window.STOP) {
                console.log('Stop!');
                return;
            }
            setTimeout(loop,opts.delay);
        }

        loop();
    };

})();
