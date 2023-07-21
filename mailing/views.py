from django.db.models import Count
from loguru import logger
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from mailing import serializers
from mailing import models
from .create_mailing import RunMailing
from .celeryApp import app as celeryApp

logger.add('mailing.log', format="{time} {level} {message}",
           level="ERROR", rotation='10 MB', compression="zip")



class ClientAPI(APIView):

    @staticmethod
    @logger.catch()
    def get(request: object) -> Response:
        snippets = models.Client.objects.all()
        serializer = serializers.ClientSerializer(snippets, many=True)
        return Response(serializer.data)

    @staticmethod
    @logger.catch()
    def post(request: object) -> Response:
        """
        insert clients
        @param request.data
            {
                "id": 1,
                "mobile_number": 79066025875,
                "mobile_code": "+7",
                "tag": "1",
                "timezone": "GMT+3"
            }
        ]
        @param request:[list]
        [
            {
                "id": 1,
                "mobile_number": 79066025875,
                "mobile_code": "+7",
                "tag": "1",
                "timezone": "GMT+3"
            },
            {
                "id": 2,
                "mobile_number": 79192582246,
                "mobile_code": "+7",
                "tag": "1",
                "timezone": "GMT+4"
            }
        ]
        """
        for row in request.data:
            serializer = serializers.ClientSerializer(data=row)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Create client id - {serializer.data['id']}")
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'insert': f'{len(request.data)} elements'})

    @staticmethod
    @logger.catch()
    def delete(request: object) -> Response:
        """
        delete clients
        @param request:
        [
            {
                "id": 1
            }
        ]
        """
        if 'id' in request.data:
            models.Client.objects.filter(id=request.data['id']).delete()
            logger.info(f"Delete client id - {request.data['id']}")
            return Response({'delete_client_id': request.data['id']})
        else:
            return Response({'error': 'id is not found in request_data'})

    @staticmethod
    @logger.catch()
    def put(request: object) -> Response:
        """
        update clients
            @param request:
            [
                {
                    "id": 1,
                    "mobile_number": 79066025875,
                    "mobile_code": "+7",
                    "tag": "1",
                    "timezone": "GMT+3"
                }
            ]
            @param request:[list]
            [
                {
                    "id": 1,
                    "mobile_number": 79066025875,
                    "mobile_code": "+7",
                    "tag": "1",
                    "timezone": "GMT+3"
                },
                {
                    "id": 2,
                    "mobile_number": 79192582246,
                    "mobile_code": "+7",
                    "tag": "1",
                    "timezone": "GMT+4"
                }
            ]
                """
        for elem in request.data:
            if 'id' not in elem:
                return Response({'error': 'id is not found in request_data'})
            try:
                models.Client.objects.filter(id=elem['id']).update(**elem)
            except Exception as error:
                return Response({'error': error})
            logger.info(f"Update client id - {elem['id']}")
        return Response({'update': f'{len(request.data)} elements'})


class MallingAPI(APIView):
    @celeryApp.task(bind=True)
    def check_param_in_mailing(self, data: dict) -> None:
        logger.info(f"Create task Celery id -{self.request.id}")
        mail = RunMailing()
        if data['tag'] and data['mobile_code']:
            mail = RunMailing()
            mail.start_mailing(
                mobile_code=data['mobile_code'],
                tag=data['tag'],
                message=data['message_text'],
                id_mailing=data['id'],
                end_time=data["day_time_end"],
                celery_id=self.request.id
            )
        else:
            if data['mobile_code']:
                mail.start_mailing(
                    mobile_code=data['mobile_code'],
                    message=data['message_text'],
                    id_mailing=data['id'],
                    end_time=data["day_time_end"],
                    celery_id=self.request.id
                )
            else:
                mail.start_mailing(
                    tag=data['tag'],
                    message=data['message_text'],
                    id_mailing=data['id'],
                    end_time=data["day_time_end"],
                    celery_id=self.request.id
                )

    @staticmethod
    def get(request: object) -> Response:
        snippets = models.Malling.objects.all()
        serializer = serializers.MallingSerializer(snippets, many=True)
        return Response(serializer.data)

    @logger.catch()
    def post(self, request: object) -> Response:
        """
        created mailings
        @param request: request[list]
        [
            {
                "id": 1,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            },
            {
                "id": 2,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            }
        ]
        @param request: request
        [
            {
                "id": 1,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            }
        ]
        """
        for row in request.data:
            serializer = serializers.MallingSerializer(data=row)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Create mailing id - {serializer.data['id']}")
                if serializer.data['mobile_code'] or serializer.data['tag']:
                    self.check_param_in_mailing.apply_async(args=(serializer.data,),
                                                            eta=serializer.data["day_time_start"])
                    logger.info(f"Create task mailing start in - {serializer.data['day_time_start']}")
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'insert': f'{len(request.data)} elements'})

    @staticmethod
    @logger.catch()
    def delete(request: object) -> Response:
        """
        delete mailings
        @param request: delete
        [
            {
                "id": 1
            }
        ]
        @return:
        """
        if 'id' in request.data:
            models.Malling.objects.filter(id=request.data['id']).delete()
            logger.info(f"Delete mailing id - {request.data['id']}")
            return Response({'delete_malling_id': request.data['id']})
        else:
            return Response({'error': 'id is not found in request'})

    @staticmethod
    @logger.catch()
    def put(request: object) -> Response:
        """
        update mailings
        @param request: request[list]
        [
            {
                "id": 1,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            },
            {
                "id": 2,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            }
        ]
        @param request: request
        [
            {
                "id": 1,
                "day_time_start": "2023-07-17T21:53:59+03:00",
                "message_text": "test message",
                "mobile_code": "+7",
                "tag": "1",
                "day_time_end": "2023-08-17T22:45:59+03:00"
            }
        ]
        """
        for elem in request.data:
            if 'id' not in elem:
                return Response({'error': 'id is not found in request_data'})
            try:
                models.Malling.objects.filter(id=elem['id']).update(**elem)
            except Exception as error:
                return Response({'error': error})
            logger.info(f"Update mailing id - {elem['id']}")
        return Response({'update': f'{len(request.data)} malling'})


class StatsAPI(APIView):
    @staticmethod
    def get(request: object) -> Response:
        """
        get statistics about mailing
        @param request: request for a specific mailing list
        http://127.0.0.1:8800/api/stats?id=1
        @param request: general statistics on created mailings and the number
        of messages sent on them, grouped by status
        http://127.0.0.1:8800/api/stats
        """
        id_param = request.GET.get('id')
        if id_param:
            message = models.Message.objects.filter(malling=id_param).values()
            return Response(message)
        mailing = models.Malling.objects.values('id')
        list_mailing = [i['id'] for i in mailing]

        mess = models.Message.objects.filter(malling__in=list_mailing)\
            .values('status', 'malling').annotate(total=Count('status'))
        logger.info(f"{mess}")
        return Response(mess)
