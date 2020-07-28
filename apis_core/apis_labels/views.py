from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import DeleteView

from .forms import LabelForm
from .models import Label


class LabelListView(generic.ListView):
	model = Label
	template_name = 'apis_labels/labels_list.html'
	context_object_name = 'object_list'

	def get_queryset(self):
		return Label.objects.order_by('label')


def label_create(request):
	if request.method == "POST":
		form = LabelForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect('apis_labels:label_list')
		else:
			return render (request, 'apis_labels/label_create.html', {'form':form})
	else:
		form = LabelForm()
		return render (request, 'apis_labels/label_create.html', {'form':form})


def label_edit(request, pk):
	instance = get_object_or_404(Label, pk=pk)
	if request.method == "POST":
		form = LabelForm(request.POST, instance=instance)
		if form.is_valid():
			form.save()
			return redirect('apis_labels:label_list')
		else:
			return render (request, 'apis_labels/label_create.html', {'form':form,'instance':instance})
	else:
		form = LabelForm(instance=instance)
		return render(request, 'apis_labels/label_create.html', {'form':form, 'instance':instance})


class LabelDelete(DeleteView):
	model = Label
	template_name = 'apis_templates/confirm_delete.html'
	success_url = reverse_lazy('apis_labels:label_list')
