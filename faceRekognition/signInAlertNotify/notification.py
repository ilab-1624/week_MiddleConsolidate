import config
from datetime import datetime

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage


class ImageMessages():
    def __init__(self, dataModel):
        self.__sourceImage = dataModel['frame']['sourceImage']
        self.__personList = dataModel['frame']['personList']
    
    def __getCarouselColumns(self, person):
        carouselColumns = []
        
        # (1) append source image in carouselColumns
        sourceImageCarouselColumn = CarouselColumn(
                                        thumbnail_image_url=self.__sourceImage['imageUrl'],
                                        title='來源影像',
                                        text='來源人數：{}\n' \
                                             '時間：{}'.format(self.__sourceImage['personCount'], datetime.fromtimestamp(int(self.__sourceImage['timestamp']+ 28800))),
                                        actions=[
                                            PostbackAction(
                                                label=' ',
                                                data='doNothing'
                                            )
                                        ]
                                    )
        
        carouselColumns.append(sourceImageCarouselColumn)
        
        # (2) append source face image in carouselColumns
        sourceFaceImageCarouselColumn = CarouselColumn(
                                            thumbnail_image_url=person['sourceFaceImage']['imageUrl'],
                                            title='來源人臉',
                                            text='平均相似度：{}%'.format(round(person['sourceFaceImage']['averageSimilarity'], 2)),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
        
        carouselColumns.append(sourceFaceImageCarouselColumn)
    
        # (3) append registration images in carouselColumns
        for index, registrationImage in enumerate(person['registrationImageList'], start=1):
            carouselColumn = CarouselColumn(
                                thumbnail_image_url=registrationImage['imageUrl'],
                                title='註冊影像{}'.format(index),
                                text='faceId：{}\n' \
                                     '相似度：{}%\n' \
                                     '時間：{}'.format(registrationImage['faceId'][0:13], round(registrationImage['similarity'], 2), datetime.fromtimestamp(int(registrationImage['timestamp']+ 28800))),
                                actions=[
                                    PostbackAction(
                                        label=' ',
                                        data='doNothing'
                                    )
                                ]
                            )
            carouselColumns.append(carouselColumn)
        
        
        return carouselColumns
    
    def getCarouselTemplates(self):
        carouselTemplates = []
        if(len(self.__personList) > 0):
            for person in self.__personList:
                carouselColumns = self.__getCarouselColumns(person=person)
                carouselTemplate = TemplateSendMessage(
                                        alt_text='收到通報訊息！',
                                        template=CarouselTemplate(
                                            columns=carouselColumns
                                        )
                                    )
                carouselTemplates.append(carouselTemplate)
        else:
            sourceImageCarouselColumn = CarouselColumn(
                                            thumbnail_image_url=self.__sourceImage['imageUrl'],
                                            title='來源影像',
                                            text='來源人數：{}\n' \
                                                 '時間：{}'.format(self.__sourceImage['personCount'], datetime.fromtimestamp(int(self.__sourceImage['timestamp']+ 28800))),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
            carouselTemplate = TemplateSendMessage(
                                    alt_text='收到通報訊息！',
                                    template=CarouselTemplate(
                                        columns=[sourceImageCarouselColumn]
                                    )
                                )
            
            carouselTemplates.append(carouselTemplate)
            
        
        return carouselTemplates
        
        
class ValidationResultMessage():
    def __init__(self, dataModel):
        self.__personCount = dataModel['signInResult']['personCount']
        self.__memberCount = dataModel['signInResult']['memberCount']
        self.__notMemberCount = dataModel['signInResult']['notMemberCount']
        self.__imageCaptureTime = datetime.fromtimestamp(int(dataModel['signInResult']['timestamp'] + 28800))
        self.__personList = dataModel['signInResult']['personList']
        self.text = None
        
    def __getPersonDetailText(self, serialNumber, person):
        memberId = person['memberId'][0:13]
        registrationImageCount = person['registrationImageCount']
        matchedImageCount = person['matchedImageCount']
        averageSimilarity = round(person['averageSimilarity'], 2)
        personDetailText = '成員【{}】：\n' \
                           '\t\t成員ID：{}\n' \
                           '\t\t註冊數量：{}\n' \
                           '\t\t匹配數量：{}\n' \
                           '\t\t平均相似度：{}%\n\n'.format(serialNumber, memberId, registrationImageCount, matchedImageCount, averageSimilarity)
                           
        return personDetailText
    
    def getTextTemplate(self):
        self.text = '成員簽到\n\n' \
                    '來源人數：{}\n' \
                    '簽到人數：{}\n' \
                    '非成員人數：{}\n' \
                    '時間：{}\n\n'.format(self.__personCount, self.__memberCount, self.__notMemberCount, self.__imageCaptureTime)
        
        index = 1
        for person in self.__personList:
            if (person['isMember'] == True):
                self.text += self.__getPersonDetailText(serialNumber=index, person=person)
                index += 1
            
        textTemplate = TextSendMessage(text=self.text)
            
        return textTemplate


class AlertNotify():
    def __init__(self, personImageMessages, validationResultMessage):
        self.__receiverLineId = config.receiverLineId
        self.__personImageMessages = personImageMessages
        self.__validationResultMessage = validationResultMessage
     
    def pushMessages(self):
        personImageTemplateMessages = self.__personImageMessages.getCarouselTemplates()
        validationResulTemplateMessage = self.__validationResultMessage.getTextTemplate()
        
        pushMessages = personImageTemplateMessages + [validationResulTemplateMessage]
        
        lineBotApi = LineBotApi(config.channelAccessToken)
        
        try:
            lineBotApi.push_message(self.__receiverLineId, pushMessages)
            pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
        
        return pushResult