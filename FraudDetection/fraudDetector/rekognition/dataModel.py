dataModel={
"frame":[{

    "frameId":"string", 
    "timestamp":"timestamp", 
    "imageurl":"string", 
    "site":"string"
}],

"behaviorDetection":{
    "personId":"string", 
    "inTime":"timestamp", 
    "outTime":"timestamp",
    "isMember":"int", 
    "stayTime":"float",
    "coordinate_x":"float",
    "coordinate_y":"float"
},
"fraudDetection":{ 
    "modelScore":"int",
    "isFraud":"int", 
    "alertMessage":"string"
}
}
