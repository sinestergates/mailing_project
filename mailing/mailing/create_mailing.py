import json
import threading

from loguru import logger
from . import models
import requests
from . import settings
import datetime
from django.utils.dateparse import parse_datetime
from .celeryApp import app as celeryApp

logger.add('mailing.log', format="{time} {level} {message}",
           level="INFO", rotation='10 MB', compression="zip")


class SendingMessages:

    def send_message_from_api(self, **kwargs) -> None:
        """
        sending messages to an external api
        @param kwargs: dict
        """
        logger.info(f"Run function send_message_from_api kwargs - {kwargs}")
        message_obj = models.Message(
            status='none',
            malling=models.Malling.objects.get(id=kwargs['id_mailing']),
            client=models.Client.objects.get(id=kwargs['client'].id)
        )
        message_obj.save()
        logger.info(f"Create message object in db id - {message_obj.id}")
        data = {
            "id": message_obj.id,
            "phone": kwargs['client'].mobile_number,
            "text": kwargs['message']
        }
        logger.info(f"Create data to an external api- {data}")
        answer_api = requests.post(
            settings.API_SERVICE + f'{int(message_obj.id)}',
            headers={
                'accept': 'application/json',
                'Authorization': f'Bearer {settings.JWT_API_SERVICE}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(data),
            timeout=30
        )
        if answer_api.ok:
            logger.info(f"Return answer is ok message id - {message_obj.id}")
            message_obj.status = 'accepted'
            message_obj.save()
            logger.info(f"Message id - {message_obj.id} change status accepted")
        else:
            logger.info(f"Message id - {message_obj.id} answer status {answer_api.status_code}")


def take_elements_by_parameter_mobile_code(mobile_code: str, filter_dict=None) -> dict:
    """
    @param mobile_code: use filter orm
    @param filter_dict: if the parameter is specified tag
    @return: objects Client
    """
    if filter_dict:
        answer = filter_dict.filter(mobile_code=mobile_code)
    else:
        answer = models.Client.objects.filter(mobile_code=mobile_code)
    return answer


def take_elements_by_parameter_tag(tag: str) -> dict:
    """
    @param tag: use filter orm
    @return: objects Client
    """
    answer = models.Client.objects.filter(tag=tag)
    return answer


class SamplingFromBase(SendingMessages):
    def create_threads_for_requests(self, kwargs):
        for client in kwargs['answer']:
            if kwargs['now'].timestamp() < parse_datetime(kwargs['end_time']).timestamp():
                thr = threading.Thread(target=self.send_message_from_api,
                                       kwargs={
                                           'client': client,
                                           'message': kwargs['message'],
                                           'id_mailing': kwargs['id_mailing']
                                       })
                thr.start()
            else:
                stop_celery = celeryApp.control.revoke(kwargs['celery_id'])
                logger.info(f"Celery task id - {kwargs['celery_id']} stop, time mailing end {stop_celery}")

    def sampling_params_from_base(
            self, message: str, id_mailing: int, end_time: str, celery_id: int, mobile_code=None, tag=None) -> dict:
        """

        @param end_time: time of end mailing
        @param celery_id: id async task
        @param message: for sanding to api
        @param id_mailing: for sanding to api
        @param mobile_code: for sanding to api
        @param tag: use filter orm
        @return: answer
        """
        answer = ''
        now = datetime.datetime.now()
        dict_kwargs = {
                'answer': answer,
                'now': now,
                'end_time': end_time,
                'message': message,
                'id_mailing': id_mailing,
                'celery_id': celery_id
            }
        if mobile_code and tag:
            answer_with_tag = take_elements_by_parameter_tag(tag)
            answer = take_elements_by_parameter_mobile_code(mobile_code, filter_dict=answer_with_tag)
            dict_kwargs['answer'] = answer
            self.create_threads_for_requests(kwargs=dict_kwargs)
        else:
            if mobile_code:
                answer = take_elements_by_parameter_mobile_code(mobile_code)
                dict_kwargs['answer'] = answer
                self.create_threads_for_requests(kwargs=dict_kwargs)
            if tag:
                answer = take_elements_by_parameter_tag(tag)
                dict_kwargs['answer'] = answer
                self.create_threads_for_requests(kwargs=dict_kwargs)
        return answer


class RunMailing(SamplingFromBase):
    def start_mailing(self, message: str, id_mailing: int, end_time: str,
                      celery_id: int, mobile_code=None, tag=None) -> None:
        """
        start_mailing
        @return: None
        """
        self.sampling_params_from_base(message, id_mailing, end_time, celery_id, mobile_code, tag)

