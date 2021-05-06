import config
from datetime import datetime

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage


class ImageMessages():
    def __init__(self, dataModel):
        self.__sourceImage = dataModel['frame']['sourceImage']
        self.__memberList = dataModel['frame']['memberList']
    
    def __getCarouselColumns(self, member):
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
                                            thumbnail_image_url=member['sourceFaceImage']['imageUrl'],
                                            title='來源人臉',
                                            text='平均相似度：{}%'.format(round(member['sourceFaceImage']['averageSimilarity'], 2)),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
        
        carouselColumns.append(sourceFaceImageCarouselColumn)
        
        
        # (3) append registration images in carouselColumns
        for index, registrationImage in enumerate(member['registrationImageList'], start=1):
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
        for member in self.__memberList:
            carouselColumns = self.__getCarouselColumns(member=member)
            carouselTemplate = TemplateSendMessage(
                                    alt_text='收到通報訊息！',
                                    template=CarouselTemplate(
                                        columns=carouselColumns
                                    )
                                )
            carouselTemplates.append(carouselTemplate)
        
        return carouselTemplates
        
        
class ValidationResultMessage():
    def __init__(self, dataModel):
        self.__memberCount = dataModel['registrationResult']['memberCount']
        self.__personCount = dataModel['registrationResult']['personCount']
        self.__memberList = dataModel['registrationResult']['memberList']
    
    def __getRegistrationImageDetailText(self, serialNumber, registrationImage):
        faceId = registrationImage['faceId'][0:13]
        similarity = round(registrationImage['similarity'], 2)
        registrationTime = datetime.fromtimestamp(int(registrationImage['timestamp']+ 28800))
        
        registrationDetailText = '\t\t註冊影像[{}]：\n' \
                                 '\t\t\t\tfaceId：{}\n' \
                                 '\t\t\t\t相似度：{}%\n' \
                                 '\t\t\t\t時間：{}\n\n'.format(serialNumber, faceId, similarity, registrationTime)
        
        return registrationDetailText
        
    def __getMemberDetailText(self, serialNumber, member):
        memberId = member['memberId'][0:13]
        registrationImageCount = member['registrationImageCount']
        matchedImageCountCount = member['matchedImageCount']
        averageSimilarity = round(member['averageSimilarity'], 2)
        
        personDetailText = '成員【{}】：\n' \
                           '\t\t成員ID：{}\n' \
                           '\t\t註冊數量：{}\n' \
                           '\t\t匹配數量：{}\n' \
                           '\t\t平均相似度：{}%\n\n'.format(serialNumber, memberId, registrationImageCount, matchedImageCountCount, averageSimilarity)
        
        for index, registrationImage in enumerate(member['registrationImageList'], start=1):
            personDetailText += self.__getRegistrationImageDetailText(serialNumber=index, registrationImage=registrationImage)
                           
        return personDetailText
    
    def getTextTemplate(self):
        self.text = '成員註冊\n\n' \
                    '成員總數：{}\n' \
                    '來源人數：{}\n\n'.format(self.__memberCount, self.__personCount)
        
        for index, member in enumerate(self.__memberList, start=1):
            self.text += self.__getMemberDetailText(serialNumber=index, member=member)
            
        textTemplate = TextSendMessage(text=self.text)
            
        return textTemplate


class AlertNotify():
    def __init__(self, memberImageMessages, validationResultMessage):
        self.__receiverLineId = config.receiverLineId
        self.__memberImageMessages = memberImageMessages
        self.__validationResultMessage = validationResultMessage
     
    def pushMessages(self):
        memberImageTemplateMessages = self.__memberImageMessages.getCarouselTemplates()
        validationResulTemplateMessage = self.__validationResultMessage.getTextTemplate()
        
        pushMessages = memberImageTemplateMessages + [validationResulTemplateMessage]
        
        lineBotApi = LineBotApi(config.channelAccessToken)
        
        try:
            lineBotApi.push_message(self.__receiverLineId, pushMessages)
            pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
        
        return pushResult