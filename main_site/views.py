from django.views.generic import TemplateView, View
from django.shortcuts import render, HttpResponseRedirect
from api.models import Journal, Price, Influence, UserSubmission
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from main_site.forms import SearchForm
import simplejson as json
from .forms import JournalInfoForm, PriceInfoForm, SubmitInfoForm
from django.contrib.auth.mixins import LoginRequiredMixin
from dal import autocomplete
from datetime import date
import datetime
import re


class IndexView(TemplateView):
    template_name = "main_site/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # finding the date of the most recent update
        context['most_recent_update'] = max([
            Price.objects.all().order_by('-date_stamp')[0].date_stamp,
            Influence.objects.all().order_by('-date_stamp')[0].date_stamp,
        ]).strftime("%m/%d/%y")
        context['most_expensive'] = Price.objects.all().order_by('-price')[:5]
        context['num_journals'] = Journal.objects.all().count()
        context['num_prices'] = Price.objects.all().count()
        context['num_influences'] = Influence.objects.all().count()

        return context


class SearchView(TemplateView):
    template_name = 'main_site/search.html'

    @staticmethod
    def _reorder(cleaned_data, results):
        # ^^ okay so there are our results now its just a matter of ordering them correctly

        # figuring out which direction to order the results
        rev = cleaned_data['order'] == "dsc"  # default to ascending

        def sort_on(result):
            # figuring out which field to sort on
            sort_by_raw = cleaned_data['sort_by']
            if sort_by_raw == 'price':
                return result['mrp'].price
            elif sort_by_raw == 'ce':
                return result['ce']
            elif sort_by_raw == 'infl':
                mri = result['mri']
                if mri:
                    return mri.article_influence
                else:
                    return 0
            else:  # default to alphabetical order
                return result['journal'].journal_name

        return sorted(results, reverse=rev, key=sort_on)

    @staticmethod
    def _get_mrp(journal):
        """
        Getting mrp (most recent price)

        Returns None if no price exists
        """
        try:
            return Price.objects.filter(journal__issn=journal.issn).order_by('-date_stamp')[0]
        except IndexError:
            return None

    @staticmethod
    def _get_mri(journal):
        """
        Getting mri (most recent influence)

        Returns 0 if no influence exists
        """
        try:
            return Influence.objects.filter(journal__issn=journal.issn).order_by('-date_stamp')[0]
        except IndexError:
            return 0

    @staticmethod
    def _get_ce(price, influence):
        if not price or not influence or not influence.article_influence:
            return None

        if price.price == 0:
            return 0
        return (1000 * float(influence.article_influence)) / float(price.price)

    @staticmethod
    def _get_results(cleaned_data):
        # figuring out which field to filter on
        search_by_raw = cleaned_data['search_by']
        if search_by_raw == 'cat':
            search_by = 'category__icontains'
        elif search_by_raw == 'issn':
            search_by = 'issn__icontains'
        elif search_by_raw == 'pub':
            search_by = 'pub_name__icontains'
        elif search_by_raw == 'cat':
            search_by = 'category__icontains'
        else:  # default to the journal name
            search_by = 'journal_name__icontains'

        return [{'journal': result,
                 'mrp': SearchView._get_mrp(result),
                 'mri': SearchView._get_mri(result),
                 'ce': SearchView._get_ce(SearchView._get_mrp(result), SearchView._get_mri(result))}
                for result in Journal.objects.filter(**{search_by: cleaned_data['search_query']})]

    def get(self, request, **kwargs):
        form = SearchForm(request.GET) #JournalNameSearchForm(request.GET)
        if form.is_valid():
            results = self._reorder(form.cleaned_data, self._get_results(form.cleaned_data))
            paginator = Paginator(results, 15)
            page = request.GET.get('page')
            try:
                results = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                results = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                results = paginator.page(paginator.num_pages)
            return render(request, 'main_site/search.html', {'form': form,
                                                             'results': results,
                                                             'request': request})
        return render(request, 'main_site/search.html', {'form': form})


class JournalNameAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Journal.objects.none()
        qs = Journal.objects.all()
        if self.q:
            qs = qs.filter(journal_name__istartswith=self.q)
        return qs        


class ResultView(TemplateView):
    template_name = 'main_site/result.html'

    def get(self, request, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)
        context['journal'] = Journal.objects.get(issn=kwargs['issn'])
        context['prices'] = Price.objects.filter(journal__issn=kwargs['issn']).order_by('date_stamp')
        infl_set = Influence.objects.filter(journal__issn=kwargs['issn'])
        context['has_influence'] = infl_set.exists()
        context['num_valid_influences'] = len(infl_set)
        sorted_infl = sorted(infl_set, key=lambda infl: infl.date_stamp)
        context['influences'] = sorted_infl

        infl_events = []
        for infl in sorted_infl:
            event = {"infl": infl.article_influence, "date": infl.date_stamp.strftime("%Y-%m-%d")}
            infl_events.append(event)
        context['events'] = json.dumps(infl_events)


        return render(request, 'main_site/result.html', context)


class JournalInfoFormView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'main_site/journalinfo.html'

    def get(self, request, **kwargs):
        return render(request, 'main_site/journalinfo.html', {'form': JournalInfoForm()})

    def post(self, request, **kwargs):
        form = JournalInfoForm(request.POST)
        if form.is_valid():
            issn = form.cleaned_data['issn']
            if not Journal.objects.filter(issn=issn).exists():
                Journal.objects.create(**form.cleaned_data)
                return HttpResponseRedirect('/success/')
        return render(request, 'main_site/journalinfo.html',
                      {'form': JournalInfoForm(),
                       'failed': True})


class PriceInfoFormView(LoginRequiredMixin, TemplateView):
    login_url = '/login/'
    template_name = 'main_site/priceinfo.html'

    def get(self, request, **kwargs):
        return render(request, 'main_site/priceinfo.html', {'form': PriceInfoForm()})

    def post(self, request, **kwargs):
        form = PriceInfoForm(request.POST)
        if form.is_valid():
            issn = form.cleaned_data['journal_id']
            if Journal.objects.filter(issn=issn).exists():
                form.cleaned_data['license'] = int(form.cleaned_data['license'])
                Price.objects.create(**form.cleaned_data)
                return HttpResponseRedirect('/success/')
        return render(request, 'main_site/priceinfo.html', 
                      {'form': PriceInfoForm(),
                       'failed': True})

class SubmitInfoFormView(TemplateView):
    template_name = 'main_site/crowdinfo.html'

    def get(self, request, **kwargs):
        return render(request, 'main_site/crowdinfo.html', {'form': SubmitInfoForm()})

    def post(self, request, **kwargs):
        errors = []
        form = SubmitInfoForm(request.POST)
        if form.is_valid():
            issn = form.cleaned_data["issn"]
            # issn validation
            if issn:
                prog = re.compile("\d{4}-\d{3}[\dX]")
                if not prog.match(issn):
                    errors.append('Invalid ISSN: Should match \d{4}-\d{3}[\dX]')
            # date validation
            date_stamp = form.cleaned_data["date_stamp"]
            if date_stamp:
                if date_stamp > date.today():
                    errors.append('Invalid Date: Should be less than or equal to todays date')
            else:
                form.cleaned_data["date_stamp"] = str(date.today())
            # price and currency validation
            price = form.cleaned_data["price"]
            currency = form.cleaned_data["currency"]
            if price:
                if currency == "none":
                    errors.append('Invalid Currency: If price is provided, currency type is required')
                if currency == "other":
                    other = form.cleaned_data["other"]
                    if not other:
                        errors.append('Invalid Currency: If other is selected, it must not be empty')
                    else:
                        if len(other) > 20:
                            errors.append("Invalid Currency: Length should be <= 20, if it is longer please email the form information to us at flourishoa@gmail.com")
                        else:
                            form.cleaned_data["currency"] = other
            # Don't insert this field as a new column
            del form.cleaned_data['other']
            if not errors:
                UserSubmission.objects.create(**form.cleaned_data)
                return HttpResponseRedirect('/success/')
        else:
            # originally was automatic form validation from forms.py but now with explicit errors
            try:
                datetime.datetime.strptime(form.data["date_stamp"], '%Y-%m-%d')
            except ValueError:
                errors.append('Invalid Date: Check that the date is in YYYY-MM-DD format')
            journal_name = form.data["journal_name"]
            if not journal_name:
                errors.append("Invalid Journal Name: Cannot be empty")
            if len(journal_name) > 150:
                errors.append("Invalid Jounal Name: Length should be <= 150, if it is longer please email the form information to us at flourishoa@gmail.com")
            pub_name = form.data["pub_name"]
            if len(pub_name) > 150:
                errors.append("Invalid Publisher Name: Length should be <= 150, if it is longer please email the form information to us at flourishoa@gmail.com")
            url = form.data["url"]
            if len(url) > 150:
                errors.append("Invalid URL: Length should be <= 150, if it is longer please email the form information to us at flourishoa@gmail.com")
            comment = form.data["comment"]
            if len(comment) > 150:
                errors.append("Invalid Additional Information: Length should be <= 150, if it is longer please email the form information to us at flourishoa@gmail.com")
        return render(request, 'main_site/crowdinfo.html',
                      {'form': form,
                       'failed': True, 'errors': errors})










