import csv
import json
import re


def dic_updater_A(toadd):
    with open("ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/utils/user_dic.txt", 'r') as ufr:
        udr=ufr.readlines()
        for rows in udr:
            words=rows.split("\t")
            if len(words)!=0:
                if words[0] in toadd:
                    toadd.remove(words[0])

    with open("ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/utils/user_dic.txt", 'a') as uf:
        for name in toadd:
            uf.write('\n'+name+"	NNG")


def dic_updater_B(label, toadd):
    with open("ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/additional_dict.csv", 'r') as afr:
        adr=csv.reader(afr)
        for rows in adr:
            if len(rows)!=0:
                if rows[0] in toadd:
                    toadd.remove(rows[0])

    with open("ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/additional_dict.csv", 'a') as af:
        ad=csv.writer(af)
        for name in toadd:
            ad.writerow([name, label])

def dic_updater(label, toadd):
    dic_updater_A(toadd)
    dic_updater_B(label, toadd)


def menu_json_maker():
    with open('ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/menu.csv', 'r') as f:
        mcsv=csv.reader(f, delimiter=';')
        menu={}
        for rows in mcsv:
            if len(rows)!=0:
                row=rows[0]
                ko=re.sub(r"[^가-힣&\s]", "", row).rstrip().lstrip()
                en=re.sub(r"[^a-zA-Z&\s]", "", row).rstrip().lstrip()
                no=re.sub(r"[^0-9]", "", row)
                if ":" in row:
                    menu[ko]=[]
                    current=ko
                else:
                    new={}
                    new["name"]=ko
                    new["eng_name"]=en
                    new["price"]=no
                    new["rec_cat"]=[]
                    new["text"]=""
                    menu[current].append(new)

    with open("ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/menu.json", "w", encoding='utf-8') as json_file:
        json.dump(menu, json_file, indent=4, ensure_ascii=False)




def letsupdate():
    with open('ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/train_tools/qna/branch.json', 'r', encoding='utf-8') as brc:
        brch=json.load(brc)
        brcsubs=[]
        for brc in brch:
            brcsubs+=brc['name']

    dic_updater("LC", brcsubs)

    with open('ds-sa-chatbot-priv/chatbot/ds-sa-chatbot/menu.json', 'r', encoding='utf-8') as f:
        menu=json.load(f)
        submenu=[]
        for cat in menu.values():
            for food in cat:
                submenu.append(food["name"])

    dic_updater("B_FOOD", submenu)

    add_list=["수신거부", "고객만족도", "기념일", "생일", "쿠폰", "재결제", "상품권"]

    dic_updater("O", add_list)

    print("업데이트 완료. train_ner_mod를 돌리시오.")

letsupdate()