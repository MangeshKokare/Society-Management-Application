from django.urls import path
from . import views
from .views import *

urlpatterns = [

    # =========================
    # AUTH (LOGIN / LOGOUT)
    # =========================

    # Default page → Login
    path('', views.login_view, name='login'),

    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),


    # =========================
    # MAIN APP PAGES
    # =========================

    path('home/', views.home, name='home'),

    path('visitors/', views.visitors, name='visitors'),
    path('deliveries/', views.deliveries, name='deliveries'),

    path('services/', views.services, name='services'),

    # AJAX toggle for Daily Help (ON / OFF)
    path(
        'services/toggle/<int:id>/',
        views.toggle_daily_help,
        name='toggle_daily_help'
    ),

#     path('community/', views.community, name='community'),

    path('emergency/', views.emergency, name='emergency'),

    path('profile/', views.profile, name='profile'),

    # DASHBOARDS
    path('resident/', views.resident_dashboard, name='resident_dashboard'),
    path("resident/visitors/", views.resident_visitors, name="resident_visitors"),
    path("resident/services/", views.resident_services, name="resident_services"),
    path("resident/notices/", views.resident_notices, name="resident_notices"),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path("visitor/approve/<int:id>/", views.approve_visitor, name="approve_visitor"),
    path("visitor/deny/<int:id>/", views.deny_visitor, name="deny_visitor"),

    path("resident/visitors/", views.resident_visitors, name="resident_visitors"),
    path("visitor/approve/<int:id>/", views.approve_visitor, name="approve_visitor"),
    path("visitor/deny/<int:id>/", views.deny_visitor, name="deny_visitor"),
    path("visitor/exit/<int:id>/", views.mark_exit, name="mark_exit"),

    path("resident/visitors/preapprove/",views.preapprove_visitor, name="preapprove_visitor" ),

    path("admin/residents/",views.admin_residents,name="admin_residents" ),
    path("society-admin/dashboard/",views.society_admin_dashboard,name="society_admin_dashboard" ),
    path("residents/", society_admin_residents, name="society_admin_residents"),
    path("analytics/", society_admin_analytics, name="society_admin_analytics"),
    path("society-admin/notices/",views.society_admin_notices,name="society_admin_notices"),

    path("society-admin/notices/create/",views.society_admin_create_announcement,name="society_admin_create_announcement"),

    path("settings/", society_admin_settings, name="society_admin_settings"),

    path("society-admin/approve-user/<int:id>/",views.approve_user, name="approve_user" ),
    path("pending-approval/", views.pending_approval, name="pending_approval" ),


    path("resident/directory/", views.resident_directory, name="resident_directory"),
    path("resident/vehicles/", views.resident_vehicles, name="resident_vehicles"),
    path("delivery/verify-otp/", views.verify_delivery_otp, name="verify_delivery_otp"),
    path("guard/help-entry/<int:id>/", views.mark_help_entry),
    path("guard/help-exit/<int:id>/", views.mark_help_exit),
    path("resident/sos/", views.send_sos, name="send_sos"),

    path('services/provider/<int:provider_id>/', views.service_provider_detail, name='service_provider_detail'),
    path('services/hire/<int:provider_id>/', views.hire_service_provider, name='hire_service_provider'),
    path('services/toggle-hired/<int:hired_id>/', views.toggle_hired_service, name='toggle_hired_service'),
    path('services/terminate/<int:hired_id>/', views.terminate_hired_service, name='terminate_hired_service'),


    # ================= SERVICE PROVIDER URLs =================
    path('service-provider/dashboard/', 
         views.service_provider_dashboard, 
         name='service_provider_dashboard'),
    
    path('service-provider/clients/', 
         views.service_provider_clients, 
         name='service_provider_clients'),
    
    path('service-provider/client/<int:hired_id>/', 
         views.service_provider_client_detail, 
         name='service_provider_client_detail'),
    
    path('service-provider/requests/', 
         views.service_provider_requests, 
         name='service_provider_requests'),
    
    path('service-provider/accept-request/<int:hired_id>/', 
         views.accept_hire_request, 
         name='accept_hire_request'),
    
    path('service-provider/decline-request/<int:hired_id>/', 
         views.decline_hire_request, 
         name='decline_hire_request'),
    
    path('service-provider/profile/', 
         views.service_provider_profile, 
         name='service_provider_profile'),



    path('community/', views.resident_notices, name='resident_notices'),
    path('community/post/create/', views.create_post, name='create_post'),
    path('community/announcement/create/', views.create_announcement, name='create_announcement'),
    path('community/poll/create/', views.create_poll, name='create_poll'),
    path('community/poll/<int:poll_id>/vote/', views.vote_poll, name='vote_poll'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),

    path('community/post/<int:post_id>/like/', views.like_post),
    path('community/post/<int:post_id>/comments/', views.get_comments),
    path('community/post/<int:post_id>/comment/add/', views.add_comment),
    
    path("society-admin/resident/<int:resident_id>/view/",views.society_admin_view_resident,name="society_admin_view_resident"),
    path("society-admin/resident/<int:resident_id>/edit/",views.society_admin_edit_resident,name="society_admin_edit_resident"),
    path("society-admin/resident/update/",views.society_admin_update_resident,name="society_admin_update_resident"),
    path("society-admin/resident/delete/",views.society_admin_delete_resident,name="society_admin_delete_resident"),

     path(
     "society-admin/guards/",
     views.society_admin_guards,
     name="society_admin_guards"
     ),

     path("society-admin/guard/<int:id>/view/", views.view_guard),
     path("society-admin/guard/<int:id>/edit/", views.edit_guard),
     path("society-admin/guard/update/", views.update_guard),
     path("society-admin/guard/delete/", views.delete_guard),



    path('guard/', views.guard_dashboard, name='guard_dashboard'),
    path('guard/entry/', views.guard_entry, name='guard_entry'),
    path('guard/visitors/', views.guard_visitors, name='guard_visitors'),
    path('guard/parcels/', views.guard_parcels, name='guard_parcels'),
    path('guard/patrol/', views.guard_patrol, name='guard_patrol'),
    
    # =========================
    # GUARD VISITOR ACTIONS
    # =========================
    
    path('guard/visitor/approve/<int:visitor_id>/', 
         views.guard_approve_visitor, 
         name='guard_approve_visitor'),
    
    path('guard/visitor/checkout/<int:visitor_id>/', 
         views.guard_checkout_visitor, 
         name='guard_checkout_visitor'),
    path("guard/visitor/verify-code/", guard_verify_visitor_code, name="guard_verify_visitor_code"),
    path("guard/visitor/checkin/<int:visitor_id>/", guard_checkin_visitor, name="guard_checkin_visitor"), 
    # =========================
    # GUARD PARCEL ACTIONS
    # =========================

    path('guard/parcel/deliver/<int:delivery_id>/',views.guard_deliver_parcel,name='guard_deliver_parcel'),

    path('guard/visitor/call/<int:visitor_id>/',views.guard_call_resident,name='guard_call_resident'),

    path("guard/profile/", views.guard_profile, name="guard_profile"),
    
    path("resident/notifications/",views.resident_notifications,name="resident_notifications"),
    
    path("guard/parcel/notify/<int:delivery_id>/",views.guard_notify_parcel,name="guard_notify_parcel"),
    
    path("resident/notification/reply/<int:notification_id>/",views.reply_to_notification,name="reply_to_notification"),
    
    path("guard/notifications/",views.guard_notifications,name="guard_notifications"),
    path("guard/notification/reply/<int:notification_id>/",views.guard_reply_to_notification,name="guard_reply_to_notification"),
    
    path("resident/vehicles/add/",views.add_vehicle,name="add_vehicle"),

     path(
     "api/vehicles/<int:vehicle_id>/delete/",
     views.delete_vehicle,
     name="delete_vehicle"
     ),

    path('guard/attendance/json/',     views.guard_attendance_json,     name='guard_attendance_json'),
    path('guard/attendance/download/', views.guard_attendance_download,  name='guard_attendance_download'),
path(
    "vehicles/<int:vehicle_id>/edit/",
    views.edit_vehicle,
    name="edit_vehicle"
),

path(
    "vehicles/<int:vehicle_id>/history/",
    views.vehicle_history,
    name="vehicle_history"
),

     path("api/vehicles/<int:vehicle_id>/", views.get_vehicle),
     path("api/vehicles/<int:vehicle_id>/update/", views.update_vehicle),
     path("api/vehicles/<int:vehicle_id>/history/",views.vehicle_history_api,name="vehicle_history_api"),

     path(
     "services/review/<int:hired_id>/",
     views.add_service_review,
     name="add_service_review"
     ),

     path(
     'guard/api/stats/',
     views.dashboard_stats_api,
     name='guard_stats_api'
     ),
     path("guard/patrol/start/", views.start_patrol, name="start_patrol"),
     path("guard/patrol/stop/", views.stop_patrol, name="stop_patrol"),
     path("guard/patrol/checkpoint/", views.mark_checkpoint, name="mark_checkpoint"),
     path("guard/checkpoints/add/", views.add_checkpoint, name="add_checkpoint"),
     path("guard/patrol/scan/", views.scan_checkpoint, name="scan_checkpoint"),
     path("guard/patrol/incident/", views.report_incident, name="report_incident"),
     path("guard/complete-handover/", views.complete_handover, name="complete_handover"),


     # Guard Admin Management
     path('guard/admin/management/', views.guard_admin_management, name='guard_admin_management'),
     path('guard/admin/filter-attendance/', views.filter_attendance, name='filter_attendance'),
     path('guard/admin/export-attendance/', views.export_attendance, name='export_attendance'),
     path('guard/admin/patrol-status/', views.patrol_status_api, name='patrol_status_api'),
     path('guard/admin/shift-reports/', views.view_shift_history, name='view_shift_history'),
     path('guard/admin/generate-schedule/', views.generate_weekly_schedule, name='generate_weekly_schedule'),
     path(
     'guard/admin/create-shift/',
     views.create_shift,
     name='create_shift'
     ),
     path(
     "guard/admin/shift/<int:shift_id>/",
     views.shift_detail,
     name="shift_detail"
     ),
    path(
        "guard/admin/attendance/override/",
        views.override_attendance,
        name="override_attendance"
    ),







    path(
        "guard/admin/patrol/checkpoint-coverage/",
        views.checkpoint_coverage_api,
        name="checkpoint_coverage_api"
    ),
    path(
        "guard/admin/patrol/recent-history/",
        views.recent_patrol_history_api,
        name="recent_patrol_history_api"
    ),
    path(
        "guard/admin/patrol/stats/",
        views.patrol_stats_api,
        name="patrol_stats_api"
    ),

    # ================= PATROL – PAGES =================
    path(
        "guard/admin/patrol/<int:patrol_id>/",
        views.patrol_detail,
        name="patrol_detail"
    ),
    path(
        "guard/admin/patrol-history/",
        views.patrol_history,
        name="patrol_history"
    ),

    path('guard/check-in/', views.guard_check_in, name='guard_check_in'),
    path('guard/check-out/', views.guard_check_out, name='guard_check_out'),
    path('guard/shift-status/', views.get_shift_status, name='get_shift_status'),



    path('guard/send-message/', views.guard_send_message, name='guard_send_message'),
    path('guard/get-messages/', views.guard_get_messages, name='guard_get_messages'),
    path('guard/admin/create-custom-shift/', views.guard_admin_create_custom_shift, name='guard_admin_create_custom_shift'),


    # Get all chats for current user
    path('api/chats/', views.get_chats, name='api_get_chats'),
    
    # Get messages for a specific chat
    path('api/chats/<int:chat_id>/messages/', views.get_chat_messages, name='api_get_chat_messages'),
    
    # Send a message in a chat
    path('api/chats/<int:chat_id>/send/', views.send_message, name='api_send_message'),
    
    # Mark chat as read
    path('api/chats/<int:chat_id>/mark-read/', views.mark_chat_as_read, name='api_mark_chat_read'),
    
    # Get society members for new chat
    path('api/society-members/', views.get_society_members, name='api_society_members'),
    
    # Create or get existing chat
    path('api/chats/create/', views.create_or_get_chat, name='api_create_chat'),
    
    # Get user online status
    path('api/users/<int:user_id>/status/', views.get_user_status, name='api_user_status'),
    
    # Update current user's online status
    path('api/update-online-status/', views.update_online_status, name='api_update_online_status'),
    
    # Set user offline
    path('api/set-offline-status/', views.set_offline_status, name='api_set_offline_status'),
    
    # ========== NOTIFICATION PAGES ==========
    
    # Service Provider notifications
    path('service-provider/notifications/', views.service_provider_notifications, name='service_provider_notifications'),
    
    # Society Admin notifications
    path('society-admin/notifications/', views.society_admin_notifications, name='society_admin_notifications'),
    


    path('guard/leave/apply/', views.guard_apply_leave, name='guard_apply_leave'),
    path('guard/admin/leave/approve/<int:leave_id>/',  views.guard_admin_approve_leave,  name='guard_admin_approve_leave'),
    path('guard/admin/leave/reject/<int:leave_id>/',   views.guard_admin_reject_leave,   name='guard_admin_reject_leave'),
    path('guard/admin/leaves/', views.guard_admin_leaves_page, name='guard_admin_leaves_page'),

    path('get-society-members/',               views.get_society_members,         name='get_society_members'),
    path('chat/create-or-get/',                views.create_or_get_chat,          name='create_or_get_chat'),

    path('guard/chats/',              views.guard_chat_list, name='guard_chat_list'),
    path('guard/chat/<int:chat_id>/', views.guard_chat_room, name='guard_chat_room'),

    path('api/unread-count/', unread_count_api, name='unread_count_api'),

    path('api/bills/create/',           views.api_create_bill,   name='api_create_bill'),
    path('api/bills/<int:bill_id>/',    views.api_bill_detail,   name='api_bill_detail'),
    path('api/bills/<int:bill_id>/remind/', views.api_bill_remind, name='api_bill_remind'),
    path('api/bills/<int:bill_id>/delete/', views.api_bill_delete, name='api_bill_delete'),
    path('api/bills/pay/<int:bp_id>/', views.api_resident_pay_bill, name='api_resident_pay_bill'),

    path('api/chats/mark-all-read/', views.api_mark_all_chats_read),
]
