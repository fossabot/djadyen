# DjAdyen

[![PyPI version](https://badge.fury.io/py/djadyen.svg)](https://badge.fury.io/py/djadyen)
[![PyPI](https://img.shields.io/pypi/dm/Django.svg)](https://pypi.python.org/pypi/djadyen/0.1.7)

[![Build Status](https://travis-ci.org/maykinmedia/djadyen.svg?branch=master)](https://travis-ci.org/maykinmedia/djadyen)
[![codecov](https://codecov.io/gh/maykinmedia/djadyen/branch/master/graph/badge.svg)](https://codecov.io/gh/maykinmedia/djadyen)
[![Lintly](https://lintly.com/gh/maykinmedia/djadyen/badge.svg)](https://lintly.com/gh/maykinmedia/djadyen/)
[![Code Climate](https://codeclimate.com/github/codeclimate/codeclimate/badges/gpa.svg)](https://codeclimate.com/github/maykinmedia/djadyen)

This module is used to connect your django application to the payment provider Adyen.
Before working with this module please also read the [documentation on Adyen](https://docs.adyen.com/developers/hpp-manual).

This is only tested on a postgres database.

## Installation

Install with pip
```shell
pip install djadyen
```

Add *'adyen'* to the installed apps
```python
# settings.py

INSTALLED_APPS = [
    ...
    'djadyen',
    ...
]
```

Add the Adyen notifications urls (This is not required). These url will save all the notifications to the database. You need to make an implementation to handle the notifications
```python
# urls.py

urlpatterns = [
    ...
    url(r'^adyen/notifications/', include('djadyen.notifications.urls', namespace='adyen-notifications')),
    ...
]
```

## Usage

### Management command
There is a management command that will sync the payment methods for you. This can be used if you want the users to select a payment method/issuer on your own site.

`manage.py sync_payment_methods`

### Required settings
- `ADYEN_HOST_URL` *This is used for creating the return url from adyen*
- `ADYEN_MERCHANT_ACCOUNT` *This is the merchant accont that is used in Adyen.*
- `ADYEN_MERCHANT_SECRET` *This is the secret that is used to calculate the signature.*
- `ADYEN_SKIN_CODE` *This is the code that is generated by the skin in the Adyen application.*

### Optional settings
- `ADYEN_CURRENCYCODE` *(default='EUR') This can be set to any other currency Adyen supports*
- `ADYEN_ENABLED` *(default=True) This can be set to false for integration tests*
- `ADYEN_NEXT_STATUS` *(default='AUTHORISED') This is used for the tests. This means that the payment is accepted.*
- `ADYEN_REFETCH_OLD_STATUS` *(default=False) This is so you will always have the latest saved status. This will cause an extra db query!*
- `ADYEN_SESSION_MINUTES` *(default=10) This is how long an Adyen session is valid.*
- `ADYEN_URL` *(default='https://test.adyen.com/') This needs to be changed for the live env. This is a more secure default then entering the live env. The live env is 'https://live.adyen.com/'*

### Order object
There is an abstract order in this package. This will save you some time on creating an order for adyen.
There are some features on the order that will make it easier to integrate your order with this package.


The added fields are:

- `status` *This is the status of the object. This will be changed by adyen.*
- `created_at` *This field is used for when the order is created.*
- `reference` *This field is a communication field. It is not used outside the communication. This will be set by uuid4, but can be overwritten.*
- `psp_reference` *This field is the reference from Adyen. With this field you are able to search in the Adyen inderface.*
- `payment_option` *This is the Adyen payment option from this package.*
- `issuer` *This is the Adyen issuer from this package.*

### AdyenRedirectView
This is used to redirect to Adyen. This will also contain a redirect view. You can overwrite it if you want a styled view.
You need to provide the data that the redirect view requires. You can provide the data in different ways.

This is the integrated version. You don't have to do a lot of custom work.
```python
from djadyen.views import AdyenRedirectView


class MyAdyenRequestView(AdyenRedirectView):
    model = MyModel

    def get_form_kwargs(self):
        order = self.get_object()
        params = self.get_signed_order_params(order)

        kwargs = super(MyAdyenRequestView, self).get_form_kwargs()
        kwargs.update({'initial': params})
        return kwargs

    def get_next_url(self): # This is to populate the resURL
        order = self.get_object()
        return reverse('my_project:confirmation', kwargs={'pk': order.id})
```

Need to change some values or want to pass extra arguments? You are better off using the view this way.
Now you have full control over the arguments.
```python
from djadyen.views import AdyenRedirectView


class MyAdyenRequestView(AdyenRedirectView):
    model = MyModel

    def get_form_kwargs(self):
        order = self.get_object()
        params = self.get_default_params(
            merchantReference=order.reference,
            paymentAmount=order.get_price_in_cents(),
            shopperEmail=order.email,
            brandCode=order.payment_option.adyen_name
            resURL='https://www.djangoproject.com/'
        )
        if order.issuer:
            params['issuerId'] = order.issuer.adyen_id

        params = self.sign_params(params)

        kwargs = super(MyAdyenRequestView, self).get_form_kwargs()
        kwargs.update({'initial': params})
        return kwargs
```

### AdyenResponseMixin
Adyen also creates a response. This will help you with catching the response. This view will check if
the response from Adyen is valid. It will also provide some usefull functions so you don't have to overwrite
anything.

In this example the order is automaticly fetched from the reference that is passed in the merchantReference.
It will also set the order in the self object for easy access. In the done function the order is saved
and the template will be rendered.
```python
from djadyen.views import AdyenResponseMixin
from djadyen.choices import Status


class ConfirmationView(AdyenResponseMixin, TemplateView):
    template_name = 'my_project/confirmation.html'
    model = Order

    def handle_authorised(self):
        self.order.status = Status.Authorised
        return self.done()

    def handle_pending(self):
        self.order.status = Status.Pending
        return self.done()

    def handle_refused(self):
        self.order.status = Status.Refused
        return self.done()

    def handle_error(self):
        self.order.status = Status.Error
        return self.done()

    def handle_canceled(self):
        self.order.status = Status.Cancel
        return self.done()

    def handle_default(self):
        if self.psp_reference:
            self.order.psp_reference = self.psp_reference
```

If you did not pass the reference of the order in the merchantReference. You might want to set the auto_fetch to False.
Now there is also no order set to self and you need to fetch the order yourself.
```python
from djadyen.views import AdyenResponseMixin
from djadyen.choices import Status


class ConfirmationView(AdyenResponseMixin, TemplateView):
    template_name = 'my_project/confirmation.html'
    auto_fetch = False

    def handle_authorised(self):
        # Do stuff

    def handle_pending(self):
        # Do stuff

    def handle_refused(self):
        # Do stuff

    def handle_error(self):
        # Do stuff

    def handle_canceled(self):
        # Do stuff

    def handle_default(self):
        # Do stuff that is required for all functions above. Like settings the psp_reference
```

# Adyen notifications

Setup the standard notifications in Adyen. These will comunicate about the payments if they were succesful or not.
This is **very important** because the notifications will be needed when a payment is redirected with a pending payment.

The notifications will be stored in the database. You need to write the handling of the notifications yourself.
