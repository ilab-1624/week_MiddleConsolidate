import notificationConfig
import json

from linebot import LineBotApi
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackAction, TextSendMessage

def lambda_handler(event, context):
    dataModel = event
    
    resultlist = event['result']

    
    for incident in resultlist:
       
        if incident['code'] == 0: # 現地場景截圖
            
            carouselColumn = CarouselColumn(
                thumbnail_image_url=incident['sourceImageUrl'],
                title='現場影像',
                text='時間：'+ str(incident['eventTime']),
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            List = [carouselColumn]
            print(incident['objectList'])
            for obj in incident['objectList']:
                carouselColumn = CarouselColumn(
                    thumbnail_image_url=obj['objectImageUrl'],
                    title='物件 : '+ str(obj['name']),
                    text='信心指數 : ' + str(round(obj['confidence'],2)) + '%',
                    actions=[
                        PostbackAction(
                            label=' ',
                            data='doNothing'
                        )
                    ]
            )
                List.append(carouselColumn)
            carouselTemplate = TemplateSendMessage(
                        alt_text='收到通報訊息！',
                        template=CarouselTemplate(
                            columns=List
                        )
                    )
                    
            #----------------------------------------------------------------- 以上code[0]的第一則推播訊息
            #-----------------------------------------------------------------
            objectCount = str(incident['objectCount'])
            eventtime = str(incident['eventTime'])
            
            tempmessage = '背景註冊\n' \
                          '\t\t物件總數 : ' + objectCount + '\n'\
                          '時間 : ' + eventtime + '\n\n'
            
            oblist = incident['objectList']
                         
            for index, objlist in enumerate(oblist, start=1):
                
                itemnumber = str(index)
                name = str(objlist['name'])
                confidence = str(round(objlist['confidence'], 2))
                coordination = {'X': str(round(objlist['coordination']['X'], 2)), 'Y': str(round(objlist['coordination']['Y'], 2))}
                
                tempmessage += '物件【' + itemnumber + '】\n'\
                               '名稱 : ' + name + '\n'\
                               '位置 : (' + coordination['X'] + ', ' +  coordination['Y'] + ')\n'\
                               '信心指數 : ' + confidence + '\n\n'
            
            

            
            textTemplate = TextSendMessage(text=tempmessage)
                    

            
            #----------------------------------------------------------------- 以上code[0]的第二則推播訊息
                
            
            pushMessages = [carouselTemplate, textTemplate] # 推兩則
    
        elif incident['code'] == 1: # 鏡頭遮蔽
            carouselColumn = CarouselColumn(
                thumbnail_image_url=incident['normalSceneImageUrl'],
                title='原始影像',
                text='時間：' + incident['normalSceneTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            
            eventColumn = CarouselColumn(
                thumbnail_image_url=incident['sourceImageUrl'],
                title='事件警示 : ' + incident['event'],
                text='時間：' + incident['eventTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            message = [carouselColumn, eventColumn]
            
            carouselTemplate = TemplateSendMessage(
                        alt_text='收到通報訊息！',
                        template=CarouselTemplate(
                            columns=message
                        )
                    )
            pushMessages = [carouselTemplate] # 推一則
            
                    
    
        elif incident['code'] == 2: # 鏡頭偏移
            carouselColumn = CarouselColumn(
                thumbnail_image_url=incident['normalSceneImageUrl'],
                title='原始影像',
                text='時間：' + incident['normalSceneTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            
            eventColumn = CarouselColumn(
                thumbnail_image_url=incident['sourceImageUrl'],
                title='事件警示 : ' + incident['event'],
                text='時間：' + incident['eventTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            message = [carouselColumn, eventColumn]
            
            carouselTemplate = TemplateSendMessage(
                        alt_text='收到通報訊息！',
                        template=CarouselTemplate(
                            columns=message
                        )
                    )
            pushMessages = [carouselTemplate]
    
        elif incident['code'] == 3: # 設備遺失
            carouselColumn = CarouselColumn(
                thumbnail_image_url=incident['sourceImageUrl'],
                title='現場影像',
                text='時間：' + incident['eventTime'] +  '\n' + '遺失設備數 : ' + str(len(incident['objectList'])),
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            List = [carouselColumn]
            carouselColumn2 = CarouselColumn(
                thumbnail_image_url=incident['normalSceneImageUrl'],
                title='原始影像',
                text='時間：' + incident['normalSceneTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            List.append(carouselColumn2)
            
            for oblist in incident['objectList']:
                
                eventColumn = CarouselColumn(
                    thumbnail_image_url=oblist['objectImageUrl'],
                    title='事件警示 : ' + incident['event'],
                    text='名稱：' + oblist['name'],
                    actions=[
                        PostbackAction(
                            label=' ',
                            data='doNothing'
                        )
                    ]
                )

                List.append(eventColumn)
            message = [carouselColumn, eventColumn]
            
            carouselTemplate = TemplateSendMessage(
                        alt_text='收到通報訊息！',
                        template=CarouselTemplate(
                            columns=List
                        )
                    )
            pushMessages = [carouselTemplate] # 推一則
        
        elif incident['code'] == 4: # 物件置留
                
            carouselColumn = CarouselColumn(
                thumbnail_image_url=incident['sourceImageUrl'],
                title='現場影像',
                text='時間：' + incident['eventTime'] +  '\n' + '置留物件數 : ' + str(len(incident['objectList'])),
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            List = [carouselColumn]
            carouselColumn2 = CarouselColumn(
                thumbnail_image_url=incident['normalSceneImageUrl'],
                title='原始影像',
                text='時間：' + incident['normalSceneTime'],
                actions=[
                    PostbackAction(
                        label=' ',
                        data='doNothing'
                    )
                ]
            )
            List.append(carouselColumn2)
            for oblist in incident['objectList']:
                '''
                if oblist['longStay'] == True:
                    objecttype = '長置物'
                elif oblist['longStay'] == False:
                    objecttype = '短置物'
                '''  
                    
                eventColumn = CarouselColumn(
                    thumbnail_image_url=oblist['objectImageUrl'],
                    title='事件警示 : ' + incident['event'],
                    text='名稱：' + oblist['name'],
                    actions=[
                        PostbackAction(
                            label=' ',
                            data='doNothing'
                        )
                    ]
                )

                List.append(eventColumn)
            message = [carouselColumn, eventColumn]
            
            carouselTemplate = TemplateSendMessage(
                        alt_text='收到通報訊息！',
                        template=CarouselTemplate(
                            columns=List
                        )
                    )
            pushMessages = [carouselTemplate] # 推一則
                    
        lineBotApi = LineBotApi(notificationConfig.channelAccessToken)
        
        try:
            if len(resultlist) != 0 :
                lineBotApi.push_message(notificationConfig.receiverLineId, pushMessages)
                pushResult = 'Success'
            
        except LineBotApiError as e:
            pushResult = 'LineBotApiError: {}'.format(e.error.message)
            
        
        print(pushResult)
        alertNotify={
            "notificationResult":{
                "linePushResult":pushResult
            }        
        }
        
        dataModel["alertNotify"]  = alertNotify
        
    return dataModel

    
    
