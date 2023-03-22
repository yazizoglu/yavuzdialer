#!/usr/bin/env python3

import requests,psycopg2,time


#set dialer config
campaign_id = 1


def GetCampaignSettings():
    # Get All Campaign Settings From campaign_settings Database Table
    cur = conn.cursor()
    query = f"SELECT * FROM public.campaign_settings WHERE campaign_id = {campaign_id}"

    # Execute the query using the cursor
    cur.execute(query)

    # Fetch the first row as a tuple
    row = cur.fetchone()


    # Get the column names
    column_names = [desc[0] for desc in cur.description]
    campaign_settings = {column_names[i]: row[i] for i in range(len(column_names))}

    # Close the cursor and connection objects
    cur.close()
    #conn.close()

    return campaign_settings


def MakeCall(numbertodial,context,callerid):
    # Asterisk IP adresi ve port numarası
    asterisk_ip = '192.168.1.77'
    asterisk_port = '8088'

    # Asterisk API kullanıcı adı ve şifresi
    username = 'asterisk'
    password = 'asterisk'

    # API isteği için gereken parametreler
    params = {
        'endpoint': 'SIP/service_provider/' + numbertodial,
        'extension': numbertodial,
        #'context': context,
        #'priority': '1',
        'callerId': callerid,
        'app' : 'hepsidialer',
        'timeout' : 30
    }

    # API isteği için gereken URL
    url = f'http://{asterisk_ip}:{asterisk_port}/ari/channels'

    # API isteğini göndermek için requests kütüphanesini kullanıyoruz
    response = requests.post(url, auth=(username, password), params=params)


    # Yanıtı kontrol etmek için HTTP yanıt kodunu yazdırıyoruz
    print("HTTP Status Code:", response.status_code)
    print("Response Headers:", response.headers)
    print("Response Body:", response.text)
    print('Make Call Triggered')
    print(response)
    return response.status_code


# dbden total attempt sayısını al. attempti 0 olanları ve status 1 olanları getir. Sorguda hiç sonuc gelmezse total attempti 1 artırarak ilk once dbye totalattempti yaz ve sonra sorgu at.
# total attempt max attempte eşitse aramayı durdur ve arama fonksiyonundan cık.

# Main App

# Connect PostgreSQL
conn = psycopg2.connect(
    host="192.168.1.77",
    database="hepsidialer",
    user="postgres",
    password="yvz77.88"
)


try:
    # App Disabled When True
    flag = False
    while flag == False:
        campaign_settings = GetCampaignSettings()
        isenabled = campaign_settings['enabled']
        if isenabled == False:
            break


        cur = conn.cursor()
        cur.execute(
            f"SELECT * FROM public.campaign_stats WHERE campaignid = {campaign_id}")
        #totalattempt kolon sırası değişirse çalışmaz
        totalattempt = cur.fetchone()[1]
        cur.close()
        # dönen sorgudan total attempti değişkene al.

        if totalattempt == campaign_settings['maxretry']:
            break

        cur = conn.cursor()
        print(campaign_settings['campaign_name'])

        # Get Number list Before Dial
        cur.execute(
            f"SELECT * FROM public.{campaign_settings['campaign_name']} WHERE attempt = {totalattempt} LIMIT {campaign_settings['dialing_boost']}")
        rows = cur.fetchall()
        cur.close()
        number = [t[1] for t in rows]
        contactid = [t[7] for t in rows]
        attemptcount = [t[6] for t in rows]

        print(f'rows = {contactid}')

        if len(rows) == 0:
            cur = conn.cursor()
            cur.execute(
                f"UPDATE public.campaign_stats SET totalattempt = {totalattempt + 1} WHERE campaignid = {campaign_id} ")

            conn.commit()
            cur.close()

            continue
        i = 0
        #for numbera in number:
        for i in range(len(number)):
            print(f'number = {number[i]}, contactid = {contactid[i]}, attemptcount = {attemptcount[i]}')
            time.sleep(1)
            callresponse = MakeCall(number[i],campaign_settings['context'],campaign_settings['callerid'])
            cur = conn.cursor()
            cur.execute(
                f"UPDATE public.{campaign_settings['campaign_name']} SET attempt = {attemptcount[i] + 1}, status = CASE WHEN status = 1 THEN status ELSE 1 END  WHERE contactid = {contactid[i]}")
            conn.commit()
            if callresponse == 200:
                print(f"Arama Basarili {number[i]}")
                print(f"UPDATE {campaign_settings['campaign_name']} SET attempt = {attemptcount[i] + 1} WHERE contactid = {contactid[i]}")

                #i += i
    #cur.close()
    #conn.close()


except:
    print('test')
    cur.close()
    conn.close()








# Sorgu çalıştırma
#cur = conn.cursor()
#cur.execute(
#    f"SELECT number1 FROM public.{column_names[retrycount]} WHERE status IS NOT 2 and attempt < {column_names[campaign_name]} LIMIT 5")
#rows = cur.fetchall()

# numbertodial listesine numaralari aktarma
#numbertodial = [row[0] for row in rows]

# update status for picked numbers as "touched"
#query = "UPDATE " + column_names[campaign_name] + " SET status = 1 WHERE number1 = %s"

# Update the status column for each number in the row list
#for numbertodial in row:
#    cur.execute(query, (numbertodial,))

# Commit the changes to the database
#conn.commit()

# Veritabanı bağlantısını kapatma
#cur.close()
#conn.close()
