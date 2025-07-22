from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import session, redirect, url_for
from models.models import *




#Modified Admin Views

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name):
        return redirect(url_for('routes_bp.login'))

class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get('is_admin', False)

    def inaccessible_callback(self, name):
        return redirect(url_for('routes_bp.login'))

class UserAdmin(SecureModelView):
    column_list  =  ['id', 'email', 'name', 'is_admin']
    form_columns  =  ['email', 'password', 'name', 'phone', 'address', 'pincode', 'is_admin']
    can_create  =  True
    can_edit  =  False
    can_delete  =  True
    column_sortable_list  =  ['id', 'name', 'is_admin']
    column_searchable_list  =  ['id', 'email', 'name', 'phone', 'address', 'pincode']
    column_default_sort  =  'id'

class ParkingLotAdmin(SecureModelView):
    column_list  =  ['id', 'prime_location_name', 'max_spots', 'price_per_hour', 'address', 'pincode', 'is_active']
    column_searchable_list = ['prime_location_name', 'address', 'pincode']
    column_sortable_list = ['id', 'prime_location_name', 'address', 'price_per_hour', 'is_active']
    def on_model_change(self, form, model, is_created):
        db.session.flush()

        if is_created:
            for i in range(1, model.max_spots + 1):
                spot = ParkingSpot(id = f"L{model.id}_S{i}", lot_id = model.id)
                db.session.add(spot)

        else:
            old_spots = ParkingSpot.query.filter_by(lot_id = model.id).all()
            old_spots_count = len(old_spots)
            if old_spots_count != model.max_spots:
                all_unreserved = True
                for spot in old_spots:
                    if spot.is_reserved:
                        all_unreserved = False
                        break
                if not all_unreserved:
                    raise ValueError("Cannot change max spots: some spots are currently reserved.")
                
                if all_unreserved:
                    for spot in old_spots:
                        db.session.delete(spot)
                    db.session.flush()
                    for i in range(1, model.max_spots + 1):
                        new_spot = ParkingSpot(id = f"L{model.id}_S{i}", lot_id = model.id)
                        db.session.add(new_spot)





class ParkingSpotAdmin(SecureModelView):
    column_list  =  ['id', 'lot', 'is_reserved']
    form_columns  =  ['lot']
    column_sortable_list = ['id', 'is_reserved']
    column_searchable_list = ['lot.prime_location_name', 'id']
    can_edit = False
    can_create = False
    can_delete = False
    def on_model_change(self,  model, is_created):
        db.session.flush()

        if is_created:
            lot = ParkingLot.query.filter_by(id = model.lot_id).first()
            lot.max_spots += 1
            db.session.commit()
        
    

    # Use form_ajax_refs for the relationship field
    form_ajax_refs  =  {
        'lot': {
            'fields': ['prime_location_name', 'address', 'pincode', 'id'],
            'page_size': 10
        }
    }

class ReservationAdmin(SecureModelView):

    column_list  =  ['id', 'spot', 'user', 'parking_timestamp']
    # form_columns  =  ['spot', 'user', 'parking_timestamp']
    can_create  =  False
    can_edit  =  False
    can_delete  =  True
    # form_ajax_refs  =  {
    #     'spot': {
    #         'fields': ['spot_number', 'lot_id'],
    #         'page_size': 10
    #     },
    #     'user': {
    #         'fields': ['email', 'name'],
    #         'page_size': 10
    #     }
    # }
class PastReservationsAdmin(SecureModelView):
    column_list = ['id', 'user_email', 'lot_prime_location', 'address', 'pincode', 'parking_timestamp', 'leaving_timestamp', 'vehicle_number']
    column_sortable_list = ['id', 'user_email', 'lot_prime_location', 'address', 'parking_timestamp', 'leaving_timestamp', 'total_cost']
    column_searchable_list = ['user_email', 'lot_prime_location', 'address', 'pincode']
    can_create  =  False
    can_edit  =  False
    can_delete  =  True




