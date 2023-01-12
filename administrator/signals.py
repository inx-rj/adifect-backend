from django.db.models.signals import post_save
from .models import JobActivityChat,JobFeedback,Question
from django.dispatch import receiver
from notification.models import Notifications
from django.db.models import Q

@receiver(post_save, sender=JobActivityChat)
def create_chat_activity_Notification(sender, instance, created, **kwargs):
    if created:
        if instance.receiver is None:
            for i in instance.job_activity.job.job_applied.filter(Q(status=2) | Q(status=3)):
                data = Notifications.objects.create(user=i.user,notification=f'You have message from {instance.sender.get_full_name()}')
        else:
            data = Notifications.objects.create(user=instance.receiver,notification=f'You have message from {instance.sender.get_full_name()}')
        # print(data)
        return True


@receiver(post_save, sender=JobFeedback)
def create_rating_Notification(sender, instance, created, **kwargs):
    if created:
        data = Notifications.objects.create(user=instance.receiver_user,notification=f'{instance.sender_user.get_full_name()} provided you feedback for {instance.job.title}')
        return True

@receiver(post_save, sender=Question)
def create_job_question_Notification(sender, instance, created, **kwargs):
    if created:
        data = Notifications.objects.create(user=instance.job_applied.job.user,notification=f'{instance.user.get_full_name()} asked you question for job -{instance.job_applied.job.title}')
        return True