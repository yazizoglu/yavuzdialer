import websocket
import json
import time
from datetime import datetime
import requests
import main

# Asterisk API anahtarını ve uygulama adını burada tanımlayın
api_key = 'asterisk:asterisk'
app_name = 'hepsidialer'

# Asterisk API'ye bağlanmak için WebSocket kullanın
ws_url = 'ws://192.168.1.77:8088/ari/events?api_key={}&app={}'.format(api_key, app_name)
ws = websocket.create_connection(ws_url)


def Playback(call_id):
    url = f'http://192.168.1.77:8088/ari/channels/{call_id}/play'
    data = {
        'media': ['sound:tt-monkeys']
    }
    headers = {
        'Content-Type': 'application/json'
    }

    auth = ('asterisk', 'asterisk')
    response = requests.post(url, json=data, headers=headers, auth=auth)

    #if response.status_code == 200:
    #    print('Playback successfully initiated')
    #else:
    #    print('Failed to initiate playback')
    #    print(response.text)



def ChannelHangup(call_id):
    url = f'http://192.168.1.77:8088/ari/channels/{call_id}'
    auth = ('asterisk', 'asterisk')

    response = requests.delete(url, auth=auth)

    if response.status_code == 204:
        print('Channel successfully deleted')
    else:
        print('Failed to delete channel')
        print(response.text)


def Convertotime(time):
    formattedtime = datetime.fromisoformat(time)
    return(formattedtime)

call_id = ""
tempcdr = {}

while True:
    response = ws.recv()
    print('hello')
    print(response)
    event = json.loads(response)
    #print(event)
    print("Response: {}".format(json.dumps(event)))



    if event["type"] == "StasisStart":
        # Yeni bir çağrı başladı

        call_id = event['channel']['id']
        print('Incoming call from:', event['channel']['caller']['number'])


        Playback_result = Playback(call_id)

        if Playback_result == 200:
            print("Ses Dosyası Oynatıldı")


        print(f"{call_id} Call ID ile Yeni Bir Çağrı Başladı")



        # Yeni bir çağrı kaydı oluşturun
        dialstarttime = event["timestamp"]
        tempcdr[call_id] = {"dialstart_time": dialstarttime, "end_time": None}

    if event["type"] == "Dial":
        dialstring = event["dialstring"]
        print("Aranan numara: ", dialstring)

        if event["peer"]["id"] != call_id:
            dialstarttime = event["timestamp"]
            call_id = event["peer"]["id"]
            callednumber = dialstring.split("/")[1]
            print(f"Kesilmis Numara : {callednumber}")
            tempcdr[call_id] = {"dialstarttime": dialstarttime, "end_time": None, "called_number" : callednumber}


    if event['type'] == 'PlaybackFinished':
        print('Playback finished event received')
        ChannelHangup(call_id)

    if event["type"] == "StasisEnd":
        # Bir çağrı sonlandı
        print("Call ended")

        # Çağrı kimliğini al
        call_id = event["channel"]["id"]

        # Çağrının bitiş kaydet
        end_time = time.time()
        tempcdr[call_id]["end_time"] = end_time

        print(f"{end_time} Call ID'sine Sahip Çağrı Kapandı")

        # Çağrı süresini Hesaplanması Çağrı Sonrası Post Datanın Yazılması


        context = event["channel"]["dialplan"]["context"]
        print(context)

    if event["type"] == "ChannelDestroyed":
        cause = event["cause"]
        end_time = event["timestamp"]

        call_duration = Convertotime(event["timestamp"]) - Convertotime(dialstarttime)

        time_obj = datetime.strptime(str(call_duration), '%H:%M:%S.%f')

        durationseconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000

        tempcdr[call_id]["durationseconds"] = durationseconds

        callerid = event["channel"]["caller"]["number"]
        call_id = event["channel"]["id"]

        if cause != 16:
            durationseconds = 0

        print(f"{call_id},{callerid},{callednumber},'{dialstarttime}','{end_time}',{int(durationseconds)},'IVN','tt-monkeys',{cause},'test_context'")
        cur = main.conn.cursor()
        cur.execute(f"INSERT INTO public.postcalldata (callid,src,dst,start_time,end_time,callduration,calltype,ivrpromptname,callresult,context) VALUES ({call_id},{callerid},{callednumber},'{dialstarttime}','{end_time}',{durationseconds},'IVN','tt-monkeys',{cause},'test_context')")
        main.conn.commit()
        cur.close()

    #if event["type"] == "ChannelHangupRequest":
    #    print('test')


