#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.urlresolvers import reverse
from django.views.generic import TemplateView

from contact_form.views import ContactFormView as OriginalContactFormView

from pootle.core.views import AjaxResponseMixin

from .forms import ContactForm, ReportForm


SUBJECT_TEMPLATE = 'Unit #%d (%s)'
BODY_TEMPLATE = '''
Unit: %s

Source: %s

Current translation: %s

Your question or comment:
'''


class ContactFormTemplateView(TemplateView):
    template_name = 'contact_form/contact_form.html'


class ContactFormView(AjaxResponseMixin, OriginalContactFormView):
    form_class = ContactForm
    template_name = 'contact_form/xhr_contact_form.html'

    def get_context_data(self, **kwargs):
        # Provide the form action URL to use in the template that renders the
        # contact dialog.
        kwargs.update({
            'contact_form_url': reverse('pootle-contact-xhr'),
        })
        return super(ContactFormView, self).get_context_data(**kwargs)

    def get_initial(self):
        initial = super(ContactFormView, self).get_initial()

        user = self.request.user
        if user.is_authenticated():
            initial.update({
                'name': user.full_name,
                'email': user.email,
            })

        return initial

    def get_success_url(self):
        # XXX: This is unused. We don't need a `/contact/sent/` URL, but
        # the parent :cls:`ContactView` enforces us to set some value here
        return reverse('pootle-contact')


class ReportFormView(ContactFormView):
    form_class = ReportForm

    def get_context_data(self, **kwargs):
        # Provide the form action URL to use in the template that renders the
        # contact dialog.
        kwargs.update({
            'contact_form_url': reverse('pootle-contact-report-error'),
        })
        return super(ReportFormView, self).get_context_data(**kwargs)

    def get_initial(self):
        initial = super(ReportFormView, self).get_initial()

        report = self.request.GET.get('report', False)
        if report:
            try:
                from pootle_store.models import Unit
                uid = int(report)
                try:
                    unit = Unit.objects.select_related(
                        'store__translation_project__project',
                    ).get(id=uid)
                    if unit.is_accessible_by(self.request.user):
                        unit_absolute_url = self.request.build_absolute_uri(
                                unit.get_translate_url()
                            )
                        initial.update({
                            'subject': SUBJECT_TEMPLATE % (
                                unit.id,
                                unit.store.translation_project.language.code
                            ),
                            'body': BODY_TEMPLATE % (
                                unit_absolute_url,
                                unit.source,
                                unit.target
                            ),
                            'report_email': unit.store.translation_project \
                                                      .project.report_email,
                        })
                except Unit.DoesNotExist:
                    pass
            except ValueError:
                pass

        return initial
