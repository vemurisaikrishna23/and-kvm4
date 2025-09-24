# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ActivityLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    action = models.CharField(max_length=255)
    model_type = models.CharField(max_length=255, blank=True, null=True)
    model_id = models.PositiveBigIntegerField(blank=True, null=True)
    properties = models.TextField(db_collation='utf8mb4_bin', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'activity_logs'


class AdditionalCharges(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    overwrite_amount = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'additional_charges'


class AdditionalChargesDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    additional_charges = models.ForeignKey(AdditionalCharges, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    value_in_amount = models.IntegerField()
    value_in_percent = models.IntegerField()
    applicability = models.IntegerField(blank=True, null=True)
    applicability_base = models.IntegerField(blank=True, null=True, db_comment='amount, distance, quantity')
    applicability_operator = models.CharField(max_length=255, blank=True, null=True)
    applicability_value = models.CharField(max_length=255, blank=True, null=True)
    waivable = models.IntegerField()
    gst_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    effective_from = models.DateTimeField(blank=True, null=True)
    effective_till = models.DateTimeField(blank=True, null=True)
    overwrite_amount = models.IntegerField(db_comment='1 = is overwrite amount , 0 = not  overwrite amount')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'additional_charges_details'


class AppBanners(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    industry_type = models.TextField(blank=True, null=True)
    c_type = models.CharField(max_length=100, blank=True, null=True)
    cluster_subcluster = models.TextField(blank=True, null=True)
    asset_type = models.TextField(blank=True, null=True)
    order = models.IntegerField(blank=True, null=True)
    details = models.TextField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    valid_from = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    tc = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'app_banners'


class ApplicableAdditionalCharge(models.Model):
    pk = models.CompositePrimaryKey('additional_charges_id', 'applicable_type', 'applicable_id')
    additional_charges = models.ForeignKey(AdditionalCharges, models.DO_NOTHING)
    applicable_type = models.CharField(max_length=255)
    applicable_id = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'applicable_additional_charge'


class Assets(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    name = models.CharField(max_length=255)
    tag_type = models.CharField(max_length=100, blank=True, null=True)
    tag_id = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    assign_to = models.CharField(max_length=255, blank=True, null=True)
    odmeter = models.CharField(max_length=255, blank=True, null=True)
    dg_kv = models.CharField(max_length=255, blank=True, null=True)
    capacity = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'assets'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BankDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    bank_name = models.CharField(max_length=255)
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    ifsc_code = models.CharField(max_length=255)
    account_type = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'bank_details'


class ChequeTransactions(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    action = models.CharField(max_length=255, db_comment='credit/debit')
    subject_type = models.CharField(max_length=255, blank=True, null=True)
    subject_id = models.PositiveBigIntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cheque_transactions'


class Cities(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    state = models.ForeignKey('States', models.DO_NOTHING)
    district = models.ForeignKey('Districts', models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cities'


class ClusterCities(models.Model):
    city = models.ForeignKey(Cities, models.DO_NOTHING)
    cluster_type = models.CharField(max_length=255)
    cluster_id = models.PositiveBigIntegerField()

    class Meta:
        managed = False
        db_table = 'cluster_cities'


class Clusters(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    state = models.ForeignKey('States', models.DO_NOTHING)
    manager = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    sales_user = models.ForeignKey('Users', models.DO_NOTHING, related_name='clusters_sales_user_set', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clusters'


class ContactForm(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    message = models.CharField(max_length=500)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'contact_form'


class CouponRedemptions(models.Model):
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    user_id = models.PositiveBigIntegerField(blank=True, null=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING, blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon = models.ForeignKey('Coupons', models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_on = models.CharField(max_length=20, blank=True, null=True)
    redeem_at = models.DateTimeField(blank=True, null=True)
    created_by = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'coupon_redemptions'


class Coupons(models.Model):
    id = models.BigAutoField(primary_key=True)
    category_id = models.PositiveBigIntegerField()
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    industry_type = models.TextField(blank=True, null=True)
    coupon_code = models.CharField(max_length=255)
    product_id = models.TextField()
    redemption_limit = models.IntegerField()
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    rules = models.TextField(blank=True, null=True)
    tc = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_onetime = models.IntegerField(blank=True, null=True, db_comment='for used one time coupoun')

    class Meta:
        managed = False
        db_table = 'coupons'


class CreditLimits(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    previous_limit = models.DecimalField(max_digits=10, decimal_places=2)
    new_limit = models.DecimalField(max_digits=10, decimal_places=2)
    approved_by = models.ForeignKey('Users', models.DO_NOTHING, db_column='approved_by', blank=True, null=True, db_comment='Admin/User who approved the increase')
    reason = models.TextField(blank=True, null=True, db_comment='Reason for limit increase')
    status = models.CharField(max_length=8, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.BigIntegerField(blank=True, null=True)
    updated_by = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'credit_limits'


class CreditPaymentRequests(models.Model):
    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_mode = models.CharField(max_length=50)
    payment_date = models.DateField()
    order_id = models.CharField(max_length=45, blank=True, null=True, db_comment="selected order id's ")
    status = models.CharField(max_length=8, blank=True, null=True)
    created_by = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'credit_payment_requests'


class Credits(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey('Customers', models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    action = models.CharField(max_length=255, db_comment='credit/debit')
    subject_type = models.CharField(max_length=255, blank=True, null=True)
    subject_id = models.PositiveBigIntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    merchant_transaction_id = models.CharField(max_length=156, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'credits'


class Customers(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=15, blank=True, null=True)
    mobile = models.CharField(max_length=255, blank=True, null=True)
    is_business = models.IntegerField(blank=True, null=True)
    industry_type = models.CharField(max_length=255, blank=True, null=True)
    monthly_requirement = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=255, blank=True, null=True)
    bank_account_number = models.CharField(max_length=255, blank=True, null=True)
    bank_account_name = models.CharField(max_length=255, blank=True, null=True)
    gst_number = models.CharField(max_length=100, blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    payment_mode = models.CharField(max_length=100, blank=True, null=True)
    credit_limit = models.IntegerField(blank=True, null=True)
    settlement_type = models.CharField(max_length=156, blank=True, null=True)
    settlement_day = models.CharField(max_length=255, blank=True, null=True)
    interest_applicable = models.IntegerField(blank=True, null=True)
    interest = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    interest_reason = models.TextField(blank=True, null=True)
    sales_person_id = models.PositiveBigIntegerField(blank=True, null=True)
    asset_poc = models.IntegerField()
    asset_poc_start_date = models.CharField(max_length=100, blank=True, null=True)
    asset_poc_end_date = models.CharField(max_length=100, blank=True, null=True)
    fule_analytics = models.IntegerField()
    fule_analytics_start_date = models.CharField(max_length=100, blank=True, null=True)
    fule_analytics_end_date = models.CharField(max_length=100, blank=True, null=True)
    atd_storage_tank = models.IntegerField()
    atd_storage_tank_start_date = models.CharField(max_length=100, blank=True, null=True)
    atd_storage_tank_end_date = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    approved_by = models.PositiveBigIntegerField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    is_deleted = models.IntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    user_step = models.IntegerField(blank=True, null=True, db_comment='1 = category ,  2 = user detail page , 3 = business detail page 1 ,4 = business detail page 2 , 5 = set pin , 6 = set biometric ')
    company_name = models.CharField(max_length=255, blank=True, null=True)
    allow_cheque_payment = models.IntegerField(blank=True, null=True)
    cheque_limit = models.FloatField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    platform = models.CharField(max_length=255, blank=True, null=True)
    language = models.CharField(max_length=255, blank=True, null=True)
    screen_resolution = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=255, blank=True, null=True)
    app_version = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customers'


class DeliveryLocationAssets(models.Model):
    delivery_location = models.ForeignKey('DeliveryLocations', models.DO_NOTHING)
    asset_id = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_location_assets'


class DeliveryLocations(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    customer = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    sub_cluster = models.ForeignKey('SubClusters', models.DO_NOTHING, blank=True, null=True)
    primary_sourcing_outlet = models.ForeignKey('PartnerOutlets', models.DO_NOTHING, blank=True, null=True)
    primary_sourcing_outlet_distance = models.FloatField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    operational_start_time = models.TimeField(blank=True, null=True)
    operational_end_time = models.TimeField(blank=True, null=True)
    diesel_surcharge_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    vehicle_type_id = models.CharField(max_length=125, blank=True, null=True)
    is_different_company_address = models.IntegerField(blank=True, null=True)
    company_gst = models.CharField(max_length=45, blank=True, null=True)
    company_location = models.CharField(max_length=255, blank=True, null=True)
    company_sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True)
    company_sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True)
    company_locality = models.CharField(max_length=255, blank=True, null=True)
    company_administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True)
    company_administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True)
    company_country = models.CharField(max_length=255, blank=True, null=True)
    company_postal_code = models.CharField(max_length=255, blank=True, null=True)
    company_latitude = models.CharField(max_length=255, blank=True, null=True)
    company_longitude = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_pan = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_locations'


class DeliverySlots(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    delivery_type = models.ForeignKey('DeliveryTypes', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    start_time = models.CharField(max_length=255)
    end_time = models.CharField(max_length=255)
    maximum_volume = models.CharField(max_length=255)
    max_orders = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_slots'


class DeliveryTypes(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    cat_id = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'delivery_types'


class Districts(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.ForeignKey('States', models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'districts'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class FailedJobs(models.Model):
    id = models.BigAutoField(primary_key=True)
    uuid = models.CharField(unique=True, max_length=255)
    connection = models.TextField()
    queue = models.TextField()
    payload = models.TextField()
    exception = models.TextField()
    failed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'failed_jobs'


class InterestHistories(models.Model):
    id = models.BigAutoField(primary_key=True)
    order_id = models.PositiveBigIntegerField()
    customer_id = models.PositiveBigIntegerField()
    order_interest_before = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_interest = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'interest_histories'


class LocationLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    driver = models.ForeignKey('Users', models.DO_NOTHING)
    route_plans = models.ForeignKey('RoutePlans', models.DO_NOTHING)
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    address = models.CharField(max_length=255, blank=True, null=True)
    logged_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'location_logs'


class Media(models.Model):
    id = models.BigAutoField(primary_key=True)
    model_type = models.CharField(max_length=255)
    model_id = models.PositiveBigIntegerField()
    uuid = models.CharField(unique=True, max_length=36, blank=True, null=True)
    collection_name = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255, blank=True, null=True)
    disk = models.CharField(max_length=255)
    conversions_disk = models.CharField(max_length=255, blank=True, null=True)
    size = models.PositiveBigIntegerField()
    manipulations = models.JSONField()
    custom_properties = models.JSONField()
    generated_conversions = models.JSONField()
    responsive_images = models.JSONField()
    order_column = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    comment = models.CharField(max_length=512, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'media'


class Migrations(models.Model):
    migration = models.CharField(max_length=255)
    batch = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'migrations'


class ModelHasPermissions(models.Model):
    pk = models.CompositePrimaryKey('permission_id', 'model_id', 'model_type')
    permission = models.ForeignKey('Permissions', models.DO_NOTHING)
    model_type = models.CharField(max_length=255)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_permissions'


class ModelHasRoles(models.Model):
    pk = models.CompositePrimaryKey('role_id', 'model_id', 'model_type')
    role = models.ForeignKey('Roles', models.DO_NOTHING)
    model_type = models.CharField(max_length=255)
    model_id = models.PositiveBigIntegerField()

    class Meta:
        managed = False
        db_table = 'model_has_roles'


class ModelMetas(models.Model):
    id = models.BigAutoField(primary_key=True)
    belong_to_type = models.CharField(max_length=255, blank=True, null=True)
    belong_to_id = models.PositiveBigIntegerField(blank=True, null=True)
    key = models.CharField(max_length=255)
    value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'model_metas'


class ModelStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    subject_type = models.CharField(max_length=255)
    subject_id = models.PositiveBigIntegerField()
    status = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'model_statuses'


class OrderBillBreakups(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    breakup_type = models.CharField(max_length=255, blank=True, null=True)
    breakup_id = models.PositiveBigIntegerField(blank=True, null=True)
    label = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    operation = models.CharField(max_length=255, db_comment='plus/minus/waivable/na')
    metadata = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_bill_breakups'


class OrderDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    asset = models.ForeignKey(Assets, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_details'


class OrderStatuses(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey('Orders', models.DO_NOTHING)
    status = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_statuses'


class Orders(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey('Organizations', models.DO_NOTHING, blank=True, null=True)
    customer = models.ForeignKey(Customers, models.DO_NOTHING)
    delivery_location = models.ForeignKey(DeliveryLocations, models.DO_NOTHING, blank=True, null=True)
    delivery_type = models.ForeignKey(DeliveryTypes, models.DO_NOTHING, blank=True, null=True)
    delivery_slot = models.ForeignKey(DeliverySlots, models.DO_NOTHING, blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    settlement_date = models.DateField(blank=True, null=True)
    payment_method = models.CharField(max_length=255, blank=True, null=True)
    split_payment_method = models.CharField(max_length=255, blank=True, null=True)
    payment_mode = models.CharField(max_length=255, blank=True, null=True)
    total_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    delivered_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    due_amount = models.DecimalField(max_digits=10, decimal_places=2)
    overdue_interest = models.DecimalField(max_digits=10, decimal_places=2)
    total_overdue_interest = models.DecimalField(max_digits=10, decimal_places=2)
    bulk_order = models.IntegerField(blank=True, null=True)
    order_source = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=255, blank=True, null=True, db_comment='completed,pending,partial')
    order_otp = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    coupon_status = models.BigIntegerField()
    merchant_transaction_id = models.CharField(max_length=45, blank=True, null=True)
    credit_merchant_transaction_id = models.CharField(max_length=45, blank=True, null=True, db_comment='Pay remaining credit amount online this id  ')
    product_category_id = models.BigIntegerField(blank=True, null=True)
    isinterest_discount = models.IntegerField(blank=True, null=True)
    is_operational_time_delivered = models.IntegerField(blank=True, null=True, db_comment='1 = operational time wise order delivered  2 =  Slots Time wise order delivered')
    discount_amount = models.CharField(max_length=100, blank=True, null=True)
    newrate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class Organizations(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    organization_type = models.CharField(max_length=9)
    business_type = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    cin = models.CharField(max_length=100, blank=True, null=True)
    gst = models.CharField(max_length=100, blank=True, null=True)
    authorized_person_name = models.CharField(max_length=255, blank=True, null=True)
    authorized_person_email = models.CharField(max_length=255, blank=True, null=True)
    authorized_person_mobile = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=255, blank=True, null=True)
    bank_account_number = models.CharField(max_length=255, blank=True, null=True)
    bank_account_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organizations'


class Otps(models.Model):
    country_code = models.CharField(max_length=15)
    mobile = models.CharField(unique=True, max_length=255)
    otp = models.CharField(max_length=4)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'otps'


class OverdueInterestBackups(models.Model):
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(Orders, models.DO_NOTHING)
    customer = models.ForeignKey(Customers, models.DO_NOTHING)
    original_overdue_interest = models.DecimalField(max_digits=10, decimal_places=2)
    paid_overdue_interest = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    original_due_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    paid_due_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    phonepe_transaction_id = models.CharField(max_length=156, blank=True, null=True)
    status = models.CharField(max_length=7, blank=True, null=True)
    payment_status = models.CharField(max_length=7, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'overdue_interest_backups'


class PartnerOutlets(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    terminal = models.ForeignKey('Terminals', models.DO_NOTHING)
    partner = models.ForeignKey('Partners', models.DO_NOTHING)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    contact_person_name = models.TextField(blank=True, null=True)
    contact_person_mobile = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partner_outlets'


class PartnerProducts(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    partner = models.ForeignKey('Partners', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partner_products'


class Partners(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    organization_type = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    business_type = models.CharField(max_length=255, blank=True, null=True)
    cin = models.CharField(max_length=100, blank=True, null=True)
    gst = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    authorized_person_name = models.CharField(max_length=255, blank=True, null=True)
    authorized_person_email = models.CharField(max_length=255, blank=True, null=True)
    authorized_person_mobile = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=255, blank=True, null=True)
    bank_account_number = models.CharField(max_length=255, blank=True, null=True)
    bank_account_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'partners'


class PasswordResets(models.Model):
    email = models.CharField(max_length=255)
    token = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'password_resets'


class PaymentGatewayLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    subject_type = models.CharField(max_length=255, blank=True, null=True)
    subject_id = models.PositiveBigIntegerField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tracking_id = models.CharField(max_length=255, blank=True, null=True)
    bank_ref_no = models.CharField(max_length=255, blank=True, null=True)
    payment_mode = models.CharField(max_length=255, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    response = models.JSONField(blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payment_gateway_logs'


class Permissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    guard_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    policy = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'permissions'
        unique_together = (('name', 'guard_name'),)


class PersonalAccessTokens(models.Model):
    id = models.BigAutoField(primary_key=True)
    tokenable_type = models.CharField(max_length=255)
    tokenable_id = models.PositiveBigIntegerField()
    name = models.CharField(max_length=255)
    token = models.CharField(unique=True, max_length=64)
    abilities = models.TextField(blank=True, null=True)
    last_used_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'personal_access_tokens'


class PointOfContacts(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.PositiveBigIntegerField(blank=True, null=True)
    belong_to_type = models.CharField(max_length=255)
    belong_to_id = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'point_of_contacts'


class ProductCategories(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    parent_id = models.IntegerField()
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_categories'


class ProductInterestLeads(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey(ProductCategories, models.DO_NOTHING)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    customer = models.ForeignKey(Customers, models.DO_NOTHING)
    contact = models.CharField(max_length=255, blank=True, null=True)
    requirement = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_interest_leads'


class ProductRates(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    partner_outlet = models.ForeignKey(PartnerOutlets, models.DO_NOTHING, blank=True, null=True)
    rate_date = models.DateTimeField()
    rate_value = models.FloatField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_rates'


class ProductSells(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING)
    sell_status = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    subcluster_id = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'product_sells'


class Products(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    product_category = models.ForeignKey(ProductCategories, models.DO_NOTHING)
    asset_required = models.IntegerField()
    sku_uom = models.CharField(max_length=255, blank=True, null=True, db_comment='Unit of Measure')
    sku_qty = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class RefillPlans(models.Model):
    organization_id = models.PositiveIntegerField()
    route_plan_id = models.PositiveIntegerField()
    route_plan_detail_id = models.PositiveIntegerField()
    product_id = models.PositiveIntegerField()
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'refill_plans'


class RoleHasPermissions(models.Model):
    pk = models.CompositePrimaryKey('permission_id', 'role_id')
    permission = models.ForeignKey(Permissions, models.DO_NOTHING)
    role = models.ForeignKey('Roles', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'role_has_permissions'


class Roles(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    guard_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    primary_role = models.IntegerField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'
        unique_together = (('name', 'guard_name'),)


class RoutePlanDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    sequence_num = models.IntegerField(blank=True, null=True)
    route_plan = models.ForeignKey('RoutePlans', models.DO_NOTHING)
    routine_type = models.CharField(max_length=255)
    subject_type = models.CharField(max_length=255)
    subject_id = models.PositiveBigIntegerField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    delivered_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    service_time = models.CharField(max_length=255, blank=True, null=True)
    routine_time = models.TimeField(blank=True, null=True)
    reached_at = models.DateTimeField(blank=True, null=True)
    transit_time = models.CharField(max_length=255, blank=True, null=True)
    km_travelled = models.CharField(max_length=255, blank=True, null=True)
    delivery_time = models.DateTimeField(blank=True, null=True)
    performed_by = models.PositiveBigIntegerField(blank=True, null=True, db_comment='routine performed by - eg. driver id')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    action = models.CharField(max_length=45, blank=True, null=True)
    transfer_from = models.IntegerField(blank=True, null=True)
    transfer_to = models.IntegerField(blank=True, null=True)
    parent_id = models.BigIntegerField(blank=True, null=True)
    supervisor_id = models.IntegerField(blank=True, null=True)
    select_du = models.CharField(max_length=45, blank=True, null=True)
    status = models.IntegerField(blank=True, null=True, db_comment='0 InActive , 1 Active ')

    class Meta:
        managed = False
        db_table = 'route_plan_details'


class RoutePlans(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    product = models.ForeignKey(Products, models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    inventory_at_start = models.DecimalField(max_digits=10, decimal_places=2)
    plan_date = models.DateField(blank=True, null=True)
    shift = models.CharField(max_length=255, blank=True, null=True)
    total_orders = models.IntegerField(blank=True, null=True)
    total_quantity = models.IntegerField(blank=True, null=True)
    total_bill = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    category_id = models.IntegerField(blank=True, null=True)
    inventory_at_end = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'route_plans'


class SalesTargets(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    target_month = models.DateField()
    target = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    achieved_target = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sales_targets'


class Sessions(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    user_id = models.PositiveBigIntegerField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    payload = models.TextField()
    last_activity = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sessions'


class States(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'states'


class SubClusters(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    manager = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sub_clusters'


class TerminalClusters(models.Model):
    id = models.BigAutoField(primary_key=True)
    terminal = models.ForeignKey('Terminals', models.DO_NOTHING)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'terminal_clusters'


class TerminalRates(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey(Products, models.DO_NOTHING, blank=True, null=True)
    terminal = models.ForeignKey('Terminals', models.DO_NOTHING, blank=True, null=True)
    rate = models.FloatField()
    effective_date = models.DateTimeField()
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'terminal_rates'


class Terminals(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    sublocality_level_2 = models.CharField(max_length=255, blank=True, null=True, db_comment='area/sector')
    sublocality_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='city')
    locality = models.CharField(max_length=255, blank=True, null=True, db_comment='main city')
    administrative_area_level_3 = models.CharField(max_length=255, blank=True, null=True, db_comment='district')
    administrative_area_level_1 = models.CharField(max_length=255, blank=True, null=True, db_comment='state')
    country = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, blank=True, null=True)
    contact_person_name = models.TextField(blank=True, null=True)
    contact_person_mobile = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'terminals'


class Transactions(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=6)
    subject_type = models.CharField(max_length=255, blank=True, null=True)
    subject_id = models.PositiveBigIntegerField(blank=True, null=True)
    belong_to_type = models.CharField(max_length=255, blank=True, null=True)
    belong_to_id = models.PositiveBigIntegerField(blank=True, null=True)
    causer_type = models.CharField(max_length=255, blank=True, null=True)
    causer_id = models.PositiveBigIntegerField(blank=True, null=True)
    linked_transaction = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, db_comment='Id of credit type transaction')
    note = models.TextField(blank=True, null=True)
    mode = models.CharField(max_length=255, blank=True, null=True, db_comment='Transaction Mode - bank-transfer, cheque, cash')
    status = models.CharField(max_length=9, blank=True, null=True)
    transaction_date = models.DateField(blank=True, null=True)
    merchant_transaction_id = models.CharField(max_length=156, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    credit_payment_request_id = models.IntegerField(blank=True, null=True)
    is_bill_pay = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transactions'


class Users(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=15, blank=True, null=True)
    mobile = models.CharField(max_length=255)
    alternate_mobile = models.CharField(max_length=255, blank=True, null=True)
    password = models.CharField(max_length=255)
    two_factor_secret = models.TextField(blank=True, null=True)
    two_factor_recovery_codes = models.TextField(blank=True, null=True)
    two_factor_confirmed_at = models.DateTimeField(blank=True, null=True)
    remember_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'


class VehicleActivityLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    description = models.TextField()
    reference_type = models.CharField(max_length=255, blank=True, null=True)
    reference_id = models.PositiveBigIntegerField(blank=True, null=True)
    properties = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_activity_logs'


class VehicleChecklistResponseDetails(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    checklist_response = models.ForeignKey('VehicleChecklistResponses', models.DO_NOTHING, blank=True, null=True)
    checklist = models.ForeignKey('VehicleChecklists', models.DO_NOTHING, blank=True, null=True)
    value = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_checklist_response_details'


class VehicleChecklistResponses(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    route_plan_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_checklist_responses'


class VehicleChecklists(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_checklists'


class VehicleDispenserHistories(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    from_type = models.CharField(max_length=255, blank=True, null=True)
    from_id = models.PositiveBigIntegerField(blank=True, null=True)
    to_type = models.CharField(max_length=255, blank=True, null=True)
    to_id = models.PositiveBigIntegerField(blank=True, null=True)
    quantity_requested = models.FloatField(blank=True, null=True)
    quantity_dispensed = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    route_plan = models.ForeignKey(RoutePlans, models.DO_NOTHING, blank=True, null=True)
    du_readings = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_dispenser_histories'


class VehicleDrivers(models.Model):
    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(Users, models.DO_NOTHING, blank=True, null=True)
    assigned_date = models.DateField()
    shift = models.IntegerField(blank=True, null=True, db_comment='1 - first')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_drivers'


class VehicleEndLocations(models.Model):
    id = models.BigAutoField(primary_key=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    driver = models.ForeignKey(Users, models.DO_NOTHING)
    lat = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    long = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    reatch_at = models.DateTimeField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_end_locations'


class VehicleLocations(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    driver_id = models.BigIntegerField(blank=True, null=True)
    captured_at = models.DateTimeField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    accuracy = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    altitude = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    speed = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    speed_accuracy = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_locations'


class VehicleReadings(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    odometer = models.FloatField(blank=True, null=True)
    totalizer_du1 = models.FloatField(blank=True, null=True)
    totalizer_du2 = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    reference_type = models.CharField(max_length=255, blank=True, null=True)
    reference_id = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_readings'


class VehicleStockHistories(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    vehicle = models.ForeignKey('Vehicles', models.DO_NOTHING)
    product = models.ForeignKey(Products, models.DO_NOTHING)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    action = models.CharField(max_length=255, db_comment='in/out')
    subject_type = models.CharField(max_length=255, blank=True, null=True)
    subject_id = models.PositiveBigIntegerField(blank=True, null=True)
    reference_type = models.CharField(max_length=255, blank=True, null=True)
    reference_id = models.PositiveBigIntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_stock_histories'


class VehicleTypes(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicle_types'


class Vehicles(models.Model):
    id = models.BigAutoField(primary_key=True)
    organization = models.ForeignKey(Organizations, models.DO_NOTHING, blank=True, null=True)
    partner = models.ForeignKey(Partners, models.DO_NOTHING, blank=True, null=True)
    cluster = models.ForeignKey(Clusters, models.DO_NOTHING, blank=True, null=True)
    product_category_id = models.PositiveBigIntegerField(blank=True, null=True)
    vehicle_no = models.CharField(max_length=255)
    make = models.CharField(max_length=255)
    model = models.CharField(max_length=255)
    tank_capacity = models.FloatField()
    tank_dead_volume = models.FloatField()
    pump1_make = models.TextField(blank=True, null=True)
    pump1_id = models.TextField(blank=True, null=True)
    pump2_make = models.TextField(blank=True, null=True)
    pump2_id = models.TextField(blank=True, null=True)
    totalizer = models.TextField(blank=True, null=True)
    opening_odometer_time = models.DateTimeField(blank=True, null=True)
    home_depot_address = models.TextField(blank=True, null=True)
    vehicle_insurance_renewal = models.DateTimeField(blank=True, null=True)
    calibration_cert_renewal = models.DateTimeField(blank=True, null=True)
    peso_certification = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    vehicle_type = models.ForeignKey(VehicleTypes, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vehicles'


class WalletTransactions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Customers, models.DO_NOTHING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=255)
    note = models.CharField(max_length=255, blank=True, null=True)
    order_id = models.BigIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=10, blank=True, null=True)
    wallet_withdrawal = models.ForeignKey('WalletWithdrawals', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_by = models.PositiveBigIntegerField(blank=True, null=True)
    bank_name = models.CharField(max_length=45, db_collation='armscii8_general_ci', blank=True, null=True)
    phonepe_transaction_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wallet_transactions'


class WalletWithdrawals(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Customers, models.DO_NOTHING)
    bank = models.ForeignKey(BankDetails, models.DO_NOTHING, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=8)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wallet_withdrawals'


class Wallets(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(Customers, models.DO_NOTHING)
    balance = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'wallets'
