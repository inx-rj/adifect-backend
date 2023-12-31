from django.db.models.signals import post_save,pre_delete, post_delete
from .models import JobActivityChat,JobFeedback,Question,JobWorkActivity
from django.dispatch import receiver
from notification.models import Notifications
from django.db.models import Q
from agency.models import DAM

# @receiver(post_save, sender=JobActivityChat)
# def create_chat_activity_Notification(sender, instance, created, **kwargs):
#     if created:
#         if instance.receiver is None:
#             for i in instance.job_activity.job.job_applied.filter(Q(status=2) | Q(status=3)):
#                 data = Notifications.objects.create(user=i.user, company=instance.job_activity.job.company,
#                                                     notification=f'You have message from {instance.sender.get_full_name()}')
#         else:
#             data = Notifications.objects.create(user=instance.receiver, company=instance.job_activity.job.company,
#                                                 notification=f'You have message from {instance.sender.get_full_name()}')
#         return True
        # if instance:
        #     if JobActivityChat.objects.filter(job_activity__job__user=self.request.user,job_activity__job=instance.job).exists():
        #         for i in instance.job_activity.job.job_applied.filter(Q(status=2) | Q(status=3)):
        #             data = Notifications.objects.create(user=i.user, company=instance.job_activity.job.company,
        #                                             notification=f'You have message from {instance.sender.get_full_name()}')
        # elif JobActivityChat.objects.filter(job_activity__job__job_applied__user=self.request.user,job_activity__job=instance.job).exists():        
        #     data = Notifications.objects.create(user=instance.receiver, company=instance.job_activity.job.company,
        #                                         notification=f'You have message from {instance.sender.get_full_name()}')
        # # print(data)
        # return True

@receiver(post_save, sender=JobFeedback)
def create_rating_Notification(sender, instance, created, **kwargs):
    if created:
        data = Notifications.objects.create(user=instance.receiver_user,company=instance.job.company,notification=f'{instance.sender_user.get_full_name()} provided you feedback for {instance.job.title}')
        return True

@receiver(post_save, sender=Question)
def create_job_question_Notification(sender, instance, created, **kwargs):
    if created:
        data = Notifications.objects.create(user=instance.job_applied.job.user,company=instance.job_applied.job.company,notification=f'{instance.user.get_full_name()} asked you question for job -{instance.job_applied.job.title}')
        return True

@receiver(post_save, sender=DAM)
def create_DAM_Notification(sender, instance, created, **kwargs):
    if created:
        if instance.company:
            for i in instance.company.invite_company_list.filter(user__user__isnull=False):
                members_notification = Notifications.objects.create(user=i.user.user,company=instance.company,notification=f'{instance.agency.get_full_name()} has created an asset',notification_type='asset_uploaded')
        agency_notification = Notifications.objects.create(user=instance.agency,company=instance.company,notification=f'{instance.agency.get_full_name()} has created an asset',notification_type='asset_uploaded')
        print(instance.agency.get_full_name())
        return True


@receiver(post_save, sender=JobWorkActivity)
def create_WorkSubmit_Notification(sender, instance, created, **kwargs):
    if created:
        if instance.work_activity=='submit_approval':
            members_notification = Notifications.objects.create(user=instance.job_work.job_applied.job.user,company=instance.job_work.job_applied.job.company,notification=f'{instance.job_work.job_applied.user.get_full_name()} has submitted work for {instance.job_work.job_applied.job.title}')

        return True
