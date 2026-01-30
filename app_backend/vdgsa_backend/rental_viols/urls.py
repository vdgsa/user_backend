from django.urls import path

from . import views

urlpatterns = [
    path('', views.RentalHomeView.as_view(), name='rentals'),

    path('user/search', views.UserSearchViewAjax.as_view(), name='user-search'),
    path('viol/rentOut/', views.RentOutView.as_view(), name='viol-rentOut'),
    path('rentals/', views.ListRentersView.as_view(), name='list-renters'),
    path('rental/renew/<int:entry_num>/', views.RentalRenewView.as_view(), name='rental-renew'),
    path('rental/return/<int:entry_num>/', views.RentalReturnView.as_view(), name='rental-return'),
    path('rental/create/', views.RentalCreateView.as_view(), name='rental-create'),
    path('rental/attach/', views.AttachToRentalView.as_view(), name='rental-attach'),
    path('rental/submit/', views.RentalSubmitView.as_view(), name='rental-submit'),
    path('rental/upload/<int:entry_num>', views.UploadRentalView.as_view(), name='rental-upload'),
    # path('rental/view/<int:entry_num>', views.ViewRentalAgreement.as_view(), name='view-agree'),
    path('renterInfo/<int:pk>', views.ViewUserInfo.as_view(), name='renter-info'),


    path('rentals/<int:pk>/', views.RentersDetailView.as_view(), name='rental-detail'),
    path('rental/<int:pk>/', views.UpdateRentalView.as_view(), name='rental-update'),

    path('contract/<int:entry_num>', views.RentalContractView.as_view(), name='show-contract'),
    path('image/<int:picture_id>', views.ImageView.as_view(), name='show-image'),
    path('attachImage/<str:to>/<int:pk>', views.AttachImageView.as_view(), name='add-image'),
    path('deleteImage/<int:picture_id>', views.DeleteImageView.as_view(), name='delete-image'),

    path('bows/', views.ListBowsView.as_view(), name='list-bows'),

    path('bows/add/', views.AddBowView.as_view(), name='add-bow'),
    path('bows/<int:pk>/', views.BowDetailView.as_view(), name='bow-detail'),
    path('bow/<int:pk>/', views.UpdateBowView.as_view(), name='bow-update'),
    path('bow/retire/<int:pk>/', views.RetireBowView.as_view(), name='bow-retire'),
    path('bow/available/<int:pk>/', views.AvailableBowView.as_view(), name='bow-avail'),

    path('cases/', views.ListCasesView.as_view(), name='list-cases'),
    path('cases/add/', views.AddCaseView.as_view(), name='add-case'),
    path('cases/<int:pk>/', views.CaseDetailView.as_view(), name='case-detail'),
    path('case/<int:pk>/', views.UpdateCaseView.as_view(), name='case-update'),
    path('case/retire/<int:pk>/', views.RetireCaseView.as_view(), name='case-retire'),
    path('case/available/<int:pk>/', views.AvailableCaseView.as_view(), name='case-avail'),

    path('viols/', views.ViolsMultiListView.as_view(), name='list-viols'),
    path('viols/add/', views.AddViolView.as_view(), name='add-viol'),
    path('viol/attach/', views.AttachToViolView.as_view(), name='viol-attach'),
    path('viol/detach/', views.DetachFromViolView.as_view(), name='viol-detach'),
    path('viol/reserve/', views.ReserveViolView.as_view(), name='viol-reserve'),
    path('viol/retire/<int:viol_num>/', views.RetireViolView.as_view(), name='viol-retire'),
    path('viol/available/<int:viol_num>/', views.AvailableViolView.as_view(), name='viol-avail'),
    path('viol/custodian/', views.ChangeCustView.as_view(), name='cust-change'),


    path('viols/<int:pk>/', views.ViolDetailView.as_view(), name='viol-detail'),
    path('viol/update/<int:pk>/', views.UpdateViolView.as_view(), name='viol-update'),


    path('waiting/', views.ListWaitingView.as_view(), name='list-waiting'),
    path('waiting/detail/<int:pk>/', views.WaitingDetailView.as_view(), name='wait-detail'),
    path('waiting/add', views.ReserveViolView.as_view(), name='add-waiting'),
    path('waiting/<int:pk>/', views.UpdateWaitingView.as_view(), name='wait-update'),

    path('custodian/', views.ListCustodianView.as_view(), name='list-cust'),
    path('custodian/<int:pk>/', views.CustodianDetailView.as_view(), name='cust-detail'),

    path('delete/<str:class>/<int:pk>/', views.SoftDeleteView.as_view(), name='soft-delete'),

]
