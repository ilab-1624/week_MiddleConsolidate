import config
import time
from datetime import datetime

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage


class ImageMessage():
    def __init__(self, dataModel):
        self.__isMember = dataModel['behaviorDetection']['isMember']
        self.__inFrame = None
        self.__outFrame = None
        for frame in dataModel['frame']:
            if (frame['site'] == 'IN'):
                self.__inFrame = frame
                self.__inFrame['stayTime'] = abs(int(dataModel['behaviorDetection']['stayTime']))
            elif (frame['site'] == 'OUT'):
                self.__outFrame = frame
                self.__outFrame['stayTime'] = abs(int(dataModel['behaviorDetection']['stayTime']))
    
    def __getCarouselColumns(self):
        if(self.__isMember == 1):
            if(self.__inFrame == None):
                outFrameCarouselColum = CarouselColumn(
                                            thumbnail_image_url=self.__outFrame['imageUrl'],
                                            title='離去影像',
                                            text='時間：{}\n' \
                                                 '在外時間：{}秒'.format(datetime.fromtimestamp(int(self.__outFrame['timestamp'] + 28800)), self.__outFrame['stayTime']),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
                carouselColumns = [outFrameCarouselColum]
            
            else:
                outFrameCarouselColum = CarouselColumn(
                                            thumbnail_image_url=self.__outFrame['imageUrl'],
                                            title='離去影像',
                                            text='時間：{}\n'.format(datetime.fromtimestamp(int(self.__outFrame['timestamp'] + 28800))),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
                                        
                inFrameCarouselColum = CarouselColumn(
                                            thumbnail_image_url=self.__inFrame['imageUrl'],
                                            title='進入影像',
                                            text='時間：{}\n' \
                                                 '在外時間：{}秒'.format(datetime.fromtimestamp(int(self.__inFrame['timestamp'] + 28800)), self.__inFrame['stayTime']),
                                            actions=[
                                                PostbackAction(
                                                    label=' ',
                                                    data='doNothing'
                                                )
                                            ]
                                        )
                carouselColumns = [outFrameCarouselColum, inFrameCarouselColum]
        
        else:
            liveFrameCarouselColum = CarouselColumn(
                                        thumbnail_image_url=self.__inFrame['imageUrl'],
                                        title='現場影像',
                                        text='時間：{}\n' \
                                             '停留時間：{}秒'.format(datetime.fromtimestamp(int(self.__inFrame['timestamp'] + 28800)), self.__inFrame['stayTime']),
                                        actions=[
                                            PostbackAction(
                                                label=' ',
                                                data='doNothing'
                                            )
                                        ]
                                    )
                                
            carouselColumns = [liveFrameCarouselColum]
        
        return carouselColumns
    
    def getCarouselTemplate(self):
        carouselColumns = self.__getCarouselColumns()
        carouselTemplate = TemplateSendMessage(
                                alt_text='收到通報訊息！',
                                template=CarouselTemplate(
                                    columns=carouselColumns
                                )
                            )
        
        return carouselTemplate
        
        
class DetectResultMessage():
    def __init__(self, dataModel):
        self.__isMember = dataModel['behaviorDetection']['isMember']
        self.__alertMessage = dataModel['fraudDetection']['alertMessage']
        self.__personId = dataModel['behaviorDetection']['personId']
        self.__coordinate = {'X': round(dataModel['behaviorDetection']['coordinate_x'], 2), 'Y': round(dataModel['behaviorDetection']['coordinate_y'], 2)}
        self.__inTime = datetime.fromtimestamp(int(dataModel['behaviorDetection']['inTime'] + 28800)) if dataModel['behaviorDetection']['inTime'] else '—'
        self.__outTime = datetime.fromtimestamp(int(dataModel['behaviorDetection']['outTime'] + 28800)) if dataModel['behaviorDetection']['outTime'] else '—'
        self.__stayTime = abs(int(dataModel['behaviorDetection']['stayTime']))
        self.__alertTime = datetime.fromtimestamp(int(time.time() + 28800))
        self.text = None
    
    def getTextTemplate(self):
        if(self.__isMember == 1):
            self.text = '異常行為偵測\n\n' \
                        '結果：{}\n\n' \
                        '成員ID：{}\n' \
                        '離去時間：{}\n' \
                        '進入時間：{}\n' \
                        '在外時間：{}秒\n' \
                        '警示時間：{}'.format(self.__alertMessage, self.__personId, self.__outTime, self.__inTime, self.__stayTime, self.__alertTime)
        
        else:
            self.text = '異常行為偵測\n\n' \
                        '結果：{0}\n\n' \
                        '非成員ID：{1}\n' \
                        '位置：({2[X]}, {2[Y]})\n' \
                        '進入時間：{3}\n' \
                        '停留時間：{4}秒\n' \
                        '警示時間：{5}\n'.format(self.__alertMessage, self.__personId, self.__coordinate, self.__inTime, self.__stayTime, self.__alertTime)
            
        textTemplate = TextSendMessage(text=self.text)
            
        return textTemplate

class AlertNotify():
    def __init__(self, imageMessage, detectResultMessage):
        self.__receiverLineId = config.receiverLineId
        self.__imageMessage = imageMessage
        self.__detectResultMessage = detectResultMessage
     
    def pushMessages(self):
        imageTemplateMessage = self.__imageMessage.getCarouselTemplate()
        detectResulTemplateMessage = self.__detectResultMessage.getTextTemplate()
        
        lineBotApi = LineBotApi(config.channelAccessToken)
        
        try:
            lineBotApi.push_message(self.__receiverLineId, [imageTemplateMessage, detectResulTemplateMessage])
            pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
        
        return pushResult