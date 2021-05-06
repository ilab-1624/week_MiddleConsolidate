import config
from datetime import datetime

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage


class SourceImageMessage():
    def __init__(self, dataModel):
        self.__imageUrl = dataModel['capture']['sourceImageUrl']
        self.__imageCaptureTime = datetime.fromtimestamp(int(dataModel['capture']['timestamp'] + 28800))
    
    def __getCarouselColumn(self):
        carouselColumn = CarouselColumn(
                            thumbnail_image_url=self.__imageUrl,
                            title='來源影像',
                            text='時間：{}'.format(self.__imageCaptureTime),
                            actions=[
                                PostbackAction(
                                    label=' ',
                                    data='doNothing'
                                )
                            ]
                        )
        
        return carouselColumn
    
    def getCarouselTemplate(self):
        carouselColumn = self.__getCarouselColumn()
        carouselTemplate = TemplateSendMessage(
                                alt_text='收到通報訊息！',
                                template=CarouselTemplate(
                                    columns=[carouselColumn]
                                )
                            )
        
        return carouselTemplate
        
        
class ValidationResultMessage():
    def __init__(self, dataModel):
        self.__personCount = dataModel['ppeDetection']['personCount']
        self.__validPpeCount = dataModel['ppeDetection']['validPpeCount']
        self.__imageCaptureTime = datetime.fromtimestamp(int(dataModel['capture']['timestamp'] + 28800))
        self.__personList = dataModel['personList']
        self.__config = dataModel['config']
        self.text = None
    
    def __getPpeDetailText(self, person):
        ppeDetailText = ''
        serialNumber = 1
        if (self.__config['maskDetection'] == True):
            maskValidationResult = '合格' if person['ppeResult']['face']['face_cover']==True else '不合格'
            faceCoverConfidence = round(person['ppeResult']['face']['face_cover_confidence'], 2)
            ppeDetailText += '\t\t\t\t({})口罩：{}\n' \
                             '\t\t\t\t\t\t\t信心指數：{}%\n'.format(serialNumber, maskValidationResult, faceCoverConfidence)
            serialNumber += 1
        
        if (self.__config['helmetDetection'] == True):
            helmetValidationResult = '合格' if person['ppeResult']['head']['head_cover']==True else '不合格'
            headCoverConfidence = round(person['ppeResult']['head']['head_cover_confidence'], 2)
            ppeDetailText += '\t\t\t\t({})安全帽：{}\n' \
                             '\t\t\t\t\t\t\t信心指數：{}%\n'.format(serialNumber, helmetValidationResult, headCoverConfidence)
            serialNumber += 1
        
        if (self.__config['glovesDetection'] == True):
            leftGloveValidationResult = '合格' if person['ppeResult']['left_hand']['left_hand_cover']==True else '不合格'
            leftHandCoverConfidence = round(person['ppeResult']['left_hand']['left_hand_cover_confidence'], 2)
            ppeDetailText += '\t\t\t\t({})左手套：{}\n' \
                             '\t\t\t\t\t\t\t信心指數：{}%\n'.format(serialNumber, leftGloveValidationResult, leftHandCoverConfidence)
            serialNumber += 1
            
            rightGloveValidationResult = '合格' if person['ppeResult']['right_hand']['right_hand_cover']==True else '不合格'
            rightHandCoverConfidence = round(person['ppeResult']['right_hand']['right_hand_cover_confidence'], 2)
            
            ppeDetailText += '\t\t\t\t({})右手套：{}\n' \
                             '\t\t\t\t\t\t\t信心指數：{}%\n'.format(serialNumber, rightGloveValidationResult, rightHandCoverConfidence)
            
        ppeDetailText += '\n'
            
        return ppeDetailText
        
    def __getPersonDetailText(self, serialNumber, person):
        location = {'X': round(person['location']['X'], 2), 'Y': round(person['location']['Y'], 2)}
        confidence = round(person['confidence'], 2)
        validPpeResult = '合格' if person['validPpe']==True else '不合格'
        ppeDetail = self.__getPpeDetailText(person=person)
        personDetailText = '人員【{0}】：\n' \
                           '\t\t位置：({1[X]}, {1[Y]})\n' \
                           '\t\t信心指數：{2}%\n' \
                           '\t\t結果：{3}\n' \
                           '{4}'.format(serialNumber, location, confidence, validPpeResult, ppeDetail)
                           
        return personDetailText
    
    def getTextTemplate(self):
        self.text = '工安檢測\n\n' \
                    '來源人數：{}\n' \
                    '合格人數：{}\n' \
                    '時間：{}\n\n'.format(self.__personCount, self.__validPpeCount, self.__imageCaptureTime)
        
        for index, person in enumerate(self.__personList, start=1):
            self.text += self.__getPersonDetailText(serialNumber=index, person=person)
            
        textTemplate = TextSendMessage(text=self.text)
            
        return textTemplate

class AlertNotify():
    def __init__(self, sourceImageMessage, validationResultMessage):
        self.__receiverLineId = config.receiverLineId
        self.__sourceImageMessage = sourceImageMessage
        self.__validationResultMessage = validationResultMessage
     
    def pushMessages(self):
        sourceImageTemplateMessage = self.__sourceImageMessage.getCarouselTemplate()
        validationResulTemplateMessage = self.__validationResultMessage.getTextTemplate()
        
        lineBotApi = LineBotApi(config.channelAccessToken)
        
        try:
            lineBotApi.push_message(self.__receiverLineId, [sourceImageTemplateMessage, validationResulTemplateMessage])
            pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
        
        return pushResult