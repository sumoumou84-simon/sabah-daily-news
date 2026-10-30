import os
import json
import base64
import time
import datetime

my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")

# 1. 寫入 PWA 圖標
icon_content = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">'
    '<rect width="512" height="512" rx="110" fill="#0f172a"/>'
    '<rect x="100" y="90" width="312" height="332" rx="18" fill="#ffffff"/>'
    '<path d="M100 108 C100 98, 108 90, 118 90 L394 90 C404 90, 412 98, 412 108 L412 160 L100 160 Z" fill="#dc2626"/>'
    '<rect x="135" y="195" width="242" height="18" rx="6" fill="#cbd5e1"/>'
    '<rect x="135" y="235" width="160" height="14" rx="5" fill="#e2e8f0"/>'
    '<rect x="135" y="265" width="242" height="14" rx="5" fill="#e2e8f0"/>'
    '<rect x="135" y="295" width="210" height="14" rx="5" fill="#e2e8f0"/>'
    '<circle cx="340" cy="355" r="48" fill="#dc2626"/>'
    '<text x="340" y="375" font-family="-apple-system, sans-serif" font-weight="900" font-size="54" fill="#ffffff" text-anchor="middle">S</text>'
    '<text x="135" y="370" font-family="sans-serif" font-weight="900" font-size="28" fill="#0f172a">西門早報</text>'
    '</svg>'
)
with open("icon.svg", "w", encoding="utf-8") as f:
    f.write(icon_content)

# 2. 寫入 Service Worker
sw_content = "self.addEventListener('install', (e) => { self.skipWaiting(); });\nself.addEventListener('activate', (e) => { e.waitUntil(clients.claim()); });\nself.addEventListener('fetch', (e) => { e.respondWith(fetch(e.request).catch(() => caches.match(e.request))); });"
with open("sw.js", "w", encoding="utf-8") as f:
    f.write(sw_content)

# 3. 寫入 Manifest
manifest_content = {
    "name": "西門日報 | Berita Harian Simon",
    "short_name": "西門日報",
    "description": "沙巴與全馬權威早間資訊平台",
    "start_url": "./index.html",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0f172a",
    "theme_color": "#dc2626",
    "icons": [
        {
            "src": "icon.svg",
            "sizes": "192x192 512x512",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }
    ]
}
with open("manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest_content, f, ensure_ascii=False, indent=2)

# 4. 10月30日 最新新聞數據
news_items = [
    {
        "is_top": True,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=80",
        "source": "SANDAKANfm / RTM Sandakan",
        "tag_zh": "沙巴治安", "tag_bm": "Keselamatan",
        "title_zh": "【沙巴治安】山打根港口執行大規模遣返 801名非法移民出境",
        "title_bm": "801 PATI Dihantar Pulang ke Negara Asal Melalui Pelabuhan Sandakan",
        "excerpt_zh": "沙巴移民局在山打根港口展開大規模集中遣返行動，將山打根、斗湖及吧巴三地共801名無證偷渡客送返原籍國。",
        "excerpt_bm": "Seramai 801 Pendatang Asing Tanpa Izin (PATI) dihantar pulang melalui Pelabuhan Sandakan.",
        "content_zh": "【山打根訊】沙巴移民局聯手海事執法機構與警方，昨日在山打根客運碼頭港口執行今年度最大規模的遣返非法移民（PATI）專案行動。本次被遣返的801名無證外籍人士分別來自山打根、斗湖以及吧巴臨時扣留營，均已依法服刑完畢並完成原籍國使館身份核實手續。執法人員在嚴密押解下安排專船分批離港直航遣返。沙巴移民局重申將堅定貫徹邊境零容忍政策，持續肅清非法滯留者，維護東海岸公共秩序與社會穩定。",
        "content_bm": "Jabatan Imigresen Sabah menghantar pulang seramai 801 PATI dari tiga depoh tahanan (Sandakan, Tawau dan Papar) melalui Pelabuhan Sandakan ke negara asal selepas selesai proses perundangan."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=600&q=80",
        "source": "自由日報 / 消防通報",
        "tag_zh": "沙巴意外", "tag_bm": "Kemalangan",
        "title_zh": "【沙巴意外】古達樂育華小校門維修照明燈，56歲工人不慎觸電身亡",
        "title_bm": "Pekerja Maut Renjatan Elektrik Semasa Pasang Lampu di SJK(C) Lok Yuk Kudat",
        "excerpt_zh": "古達樂育華小校門發生致命工傷，一名56歲承包商外籍工人在維修校門照明燈時鐵梯碰觸高壓電纜觸電墜地不治。",
        "excerpt_bm": "Lelaki warga asing maut terkena renjatan elektrik semasa kerja penyelenggaraan lampu di pintu pagar sekolah.",
        "content_zh": "【古達訊】古達樂育華小校門昨日上午發生一起奪命工傷觸電事故。一名56歲菲律賓籍承包商工人在大門籬笆高處進行照明燈安裝與維修作業時，所使用的長梯疑不慎碰觸上方高壓電纜，瞬間遭受強烈電擊後從高處摔落地面。消拯局行動指揮中心接獲投報後於4分鐘內趕抵現場，並緊急通知沙電（SESB）切斷周邊電源展開救援。經在場醫護人員實時搶救核實，該名工人已無生命體徵，當場傷重身亡。古達警方目前已將案件列為猝死案處理。",
        "content_bm": "Seorang pekerja kontraktor warga asing berusia 56 tahun maut akibat renjatan elektrik selepas tangga yang digunakannya tersentuh kabel elektrik semasa membaiki lampu di SJK(C) Lok Yuk Kudat."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=600&q=80",
        "source": "中國報 / 關稅局",
        "tag_zh": "關稅大案", "tag_bm": "Kastam",
        "title_zh": "【關稅大案】大馬查獲4950萬走私案！起獲30台軍用AI芯片伺服器",
        "title_bm": "Kastam Rampas 30 Pelayan Cip AI Gred Ketenteraan Bernilai RM49.5 Juta",
        "excerpt_zh": "不法集團將大馬充當中轉站，把30台裝置軍用級AI芯片的伺服器假申報為電子零件企圖轉運第三國，遭關稅局一舉破獲。",
        "excerpt_bm": "Sindiket guna Malaysia sebagai hab transit untuk seludup pelayan cip AI bernilai RM49.5 juta ke negara ketiga.",
        "content_zh": "【吉隆坡訊】馬來西亞皇家關稅局成功偵破一宗國際高科技走私大案。一個跨國犯罪集團企圖將大馬打造成中轉避風港，將30台裝載軍用級以及尖端人工智能（AI）高端芯片的高性能運算伺服器，從亞洲國家暗中運抵我國後，試圖以「一般電子零件」名義虛假申報並轉運至受管制的第三國。關稅局情報組接獲線報後在貨運碼頭果斷開櫃攔截，起獲該批含稅總市值高達4950萬令吉的尖端禁運設備，目前正全方位追查在本地接應的空殼物流代理。",
        "content_bm": "Jabatan Kastam Diraja Malaysia berjaya mematahkan cubaan menyeludup 30 unit pelayan yang dilengkapi cip AI gred tentera bernilai RM49.5 juta yang diisytiharkan secara palsu sebagai komponen elektronik."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1541888946425-d0fbb186156f?auto=format&fit=crop&w=600&q=80",
        "source": "InfoTawau / 工程部",
        "tag_zh": "沙巴交通", "tag_bm": "Infrastruktur",
        "title_zh": "【沙巴交通】泛婆公路1A工期落後僅達89.5%，工程部限期發整改令",
        "title_bm": "Kemajuan Fizikal Lebuhraya Pan Borneo Fasa 1A Lewat, KKR Arah Pelan Pemulihan",
        "excerpt_zh": "沙巴泛婆公路1A標段物理進度僅達89.54%，落後於既定目標，工程部已向延誤承包商下達最後通牒限期提速。",
        "excerpt_bm": "Kementerian Kerja Raya mengarahkan kontraktor Pan Borneo Sabah Fasa 1A mengemukakan pelan pemulihan segera.",
        "content_zh": "【斗湖訊】工程部（KKR）對沙巴泛婆羅洲公路（LPB）工程進展展開全面稽核，最新評估數據顯示，目前正施工中的沙巴第1A階段整體物理施工進度僅達89.54%，明顯落後於合約排期的96.32%。工程部長已正式向下轄所有進度延誤的工程承包商發出整改指令，要求其在限期內提交具備實操性的追趕追工方案，包括增加夜間施工班次與設備人員投放，以確保這條貫穿沙巴全境的經濟命脈幹線按期交付通車。",
        "content_bm": "KKR mengeluarkan arahan tegas kepada kontraktor projek Lebuhraya Pan Borneo Sabah Fasa 1A yang lewat mencapai kemajuan fizikal 89.54% berbanding 96.32% yang dijadualkan."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=600&q=80",
        "source": "Says / Sarikeians",
        "tag_zh": "東馬商業", "tag_bm": "Perniagaan",
        "title_zh": "【東馬商業】全砂首間宜家！IKEA Kuching 官宣11月27日正式開業",
        "title_bm": "IKEA Kuching Cawangan Pertama di Sarawak Dibuka 27 November Ini",
        "excerpt_zh": "宜家官方敲定進駐東馬進程，砂拉越首間實體商場將於11月27日在古晉石角Pine Square商圈隆重開幕。",
        "excerpt_bm": "IKEA mengumumkan pembukaan gedung fizikal pertamanya di Sarawak bertempat di Pine Square Batu Kawa.",
        "content_zh": "【古晉商業訊】國際知名連鎖家居巨頭宜家（IKEA）今日正式向東馬市場發布重磅官宣，砂拉越首家也是全婆羅洲旗艦實體門市——IKEA Kuching，落實於2026年11月27日盛大開門迎客。新商場坐落於古晉石角黃金商圈 Pine Square（Pines Mall），不僅引進了全套北歐風情家具樣板間與家居訂購配送中心，更設有深受民眾喜愛的宜家經典餐廳，將大幅填補東馬地區國際大型一站式現代家居零售的空白。",
        "content_bm": "IKEA Kuching mengesahkan tarikh pembukaan rasmi pada 27 November 2026 di Pine Square, Batu Kawa, menjadi gedung IKEA fizikal pertama di wilayah Sarawak."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1580519542036-c47de6196ba5?auto=format&fit=crop&w=600&q=80",
        "source": "沙巴星洲日報 / 財經",
        "tag_zh": "外匯金融", "tag_bm": "Kewangan",
        "title_zh": "【外匯金融】美聯儲按兵不動符預期，馬幣兌美元匯率升至7周新高",
        "title_bm": "Ringgit Mengukuh ke Paras Tertinggi 7 Minggu Berbanding Dolar AS",
        "excerpt_zh": "美聯儲最新議息會議維持利率不變釋放溫和信號，令吉走勢強勁，兌美元升至7周高位，兌新元創8周新高。",
        "excerpt_bm": "Mata wang Ringgit Malaysia terus mencatatkan pengukuhan berbanding dolar AS dan dolar Singapura.",
        "content_zh": "【吉隆坡財經訊】美聯儲在結束最新的貨幣政策會議後宣布基準利率按兵不動，聲明釋放溫和貨幣路徑預期，帶動新興市場外匯資產普遍走強。馬來西亞令吉在本地及海外匯市買盤湧現，令吉兌美元即期匯率強勢突破關鍵心理阻力位，創下近7個星期以來的新高點；與此同時，馬幣兌新加坡元匯率亦同步攀升至8週以來的最高水位，有效減輕輸入型通脹壓力，提振進口商信心。",
        "content_bm": "Keputusan Rizab Persekutuan AS mengekalkan kadar faedah memberi sokongan padu kepada mata wang tempatan, melonjakkan Ringgit ke paras tertinggi 7 minggu berbanding USD."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "Winrayland / 財政部",
        "tag_zh": "民生福利", "tag_bm": "Bantuan",
        "title_zh": "【民生福利】2027 STR 援助金申請截止日敲定，務必於11月15日前提交",
        "title_bm": "Permohonan Fasa 1 STR 2027 Ditutup 11 November Ini, Segera Kemas Kini",
        "excerpt_zh": "財政部發出重要日程提醒，2027年度第一階段愛心援助金（STR）新申請與資料更新截至11月15日止。",
        "excerpt_bm": "Kementerian Kewangan mengingatkan orang ramai tarikh tutup pendaftaran STR 2027 adalah pada 15 November.",
        "content_zh": "【布城政訊】財政部關愛基本金專案辦公室發出全國通告，提醒廣大低收入群體，2027年度第一階段愛心援助金（STR）的線上新申請及個人家庭資料更新，將於今年11月15日正式截止。政府重申本輪審核將全面收緊，實施跨部門大數據核驗。符合資格但尚未提報或婚姻/收入狀況有變動的民眾，務必登錄官方門戶在截止日前完成送件，以免耽誤明年初首筆援助金的發放。",
        "content_bm": "Tarikh tutup permohonan baharu dan kemas kini maklumat Sumbangan Tunai Rahmah (STR) 2027 Fasa 1 telah ditetapkan pada 15 November 2026 melalui portal rasmi MySTR."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "談談網 / 數碼部",
        "tag_zh": "數碼便民", "tag_bm": "Digital",
        "title_zh": "【數碼便民】數碼部宣布 MyGOV APP 正式上線，手機可直接申請換大馬卡",
        "title_bm": "MyGOV APP Dilancar: Permohonan Gantian MyKad Kini Boleh Dibuat Dalam Talian",
        "excerpt_zh": "民眾無需再清晨去 JPN 門市排隊，通過全新 MyGOV 應用即可在線驗證身份完成 MyKad 補發與更換手續。",
        "excerpt_bm": "Kementerian Digital melancarkan aplikasi MyGOV bagi membolehkan penggantian MyKad secara dalam talian.",
        "content_zh": "【布城訊】數碼部長正式推介全新國家級綜合政務應用程式「MyGOV APP」。該應用深度整合了國民登記局（JPN）核心數據接口，大馬公民即日起因大馬卡損壞或日常更換，無需再親赴登記局分局抽號碼牌苦候，只需在手機端完成生物特徵與數碼身份（Digital ID）雙重認證，即可全程在線提交換卡申請並自選臨近領卡點，大幅節省民間辦事成本。",
        "content_bm": "Kementerian Digital mengumumkan pelancaran aplikasi MyGOV yang membolehkan rakyat Malaysia memohon penggantian MyKad secara dalam talian tanpa perlu beratur di kaunter JPN."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1549317661-bd32c8ce0db2?auto=format&fit=crop&w=600&q=80",
        "source": "Moretify / 陸路交通法令",
        "tag_zh": "民生警示", "tag_bm": "Undang-undang",
        "title_zh": "【民生警示】拿椅子路錐霸佔公共停車位違法，最高可罰4000或坐牢1年",
        "title_bm": "Tindakan 'Cop Parking' Guna Kerusi Boleh Didenda Sehingga RM4,000",
        "excerpt_zh": "交警與市政廳重申嚴厲執法，任何人擅自使用塑膠椅、障礙物人肉霸位均觸犯法令，違者面臨重罰。",
        "excerpt_bm": "Perbuatan meletakkan halangan bagi menempah petak parkir awam merupakan kesalahan jenayah.",
        "content_zh": "【吉隆坡訊】針對商業區街道頻繁出現的「拿椅子霸車位（Cop Parking）」惡習，執法當局再次發布嚴正法律科普。根據《1987年陸路交通法令》第50(3)條文，任何人非法阻礙公共道路或公共停車位以保留停車權利均屬刑事罪行。違例者一旦罪成，初犯即可面臨最高4000令吉的罰款或長達12個月的監禁處罰。市政廳呼籲公眾遇此情況可即時拍照定位舉報，由執法人員到場移走障礙物並開出傳票。",
        "content_bm": "Pihak berkuasa menegaskan bahawa tindakan meletakkan kerusi, kon atau halangan untuk 'cop parking' adalah kesalahan di bawah Seksyen 50(3) Akta Pengangkutan Jalan 1987 yang membawa denda hingga RM4,000."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "風采 / 衛生部",
        "tag_zh": "公共醫療", "tag_bm": "Kesihatan",
        "title_zh": "【公共醫療】衛生部推行醫療服務外包見效，公立心臟手術等候期縮短數月",
        "title_bm": "KKM: Khidmat Luar Hospital Swasta Berjaya Singkatkan Waktu Menunggu Pembedahan",
        "excerpt_zh": "衛生部長祖基菲里透露，政府將部分手術外包私人醫院協同分流後，病患等候週期大幅縮短2至10週以上。",
        "excerpt_bm": "Kementerian Kesihatan berjaya memendekkan tempoh menunggu pembedahan melalui penyumberan luar ke hospital swasta.",
        "content_zh": "【布城醫療訊】衛生部長拿督斯里祖基菲里阿末在國會答詢時透露，衛生部自去年推動的「公共醫療服務外包私立醫院」試點專案取得突破性進展。針對以往公立大醫院動輒排隊等上一兩年的心臟搭橋與複雜心導管手術，在政府資助病患轉診至合約私立專科醫院後，病患整體平均等候時間已大幅縮短2至10週以上，切實化解了公立專科病房長期飽和的醫療痛點。",
        "content_bm": "Menteri Kesihatan Datuk Seri Dr Dzulkefly Ahmad mengesahkan inisiatif penyumberan luar rawatan ke hospital swasta berjaya memendekkan tempoh menunggu pembedahan kritikal seperti jantung."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "自由日報 / 砂議會",
        "tag_zh": "東馬政局", "tag_bm": "Politik",
        "title_zh": "【東馬政局】砂拉越州議會正式解散，法定60天內將舉行全州大選",
        "title_bm": "Dewan Undangan Negeri Sarawak Bubar, Pilihan Raya Negeri Dalam 60 Hari",
        "excerpt_zh": "砂拉越總理公署宣布州議會正式解散，大馬選委會將在兩週內召開特別會議敲定第13屆砂州選舉提名與投票日。",
        "excerpt_bm": "DUN Sarawak dibubarkan secara rasmi membuka laluan kepada Pilihan Raya Negeri ke-13.",
        "content_zh": "【古晉訊】砂拉越州議會昨日依憲正式宣告解散，標誌著第13屆砂拉越州選舉正式拉開戰幕。根據砂拉越州憲法規定，州選舉必須在議會解散之日起的60天內完成舉行。馬來西亞選舉委員會（SPR）預料將在近期接獲議長正式解散公函後召開特別工作會議，全面敲定全州82個州選區的候選人提名日、競選期以及選民投票日日程表。",
        "content_bm": "Dewan Undangan Negeri (DUN) Sarawak telah dibubarkan secara rasmi bagi membolehkan Pilihan Raya Negeri (PRN) Ke-13 diadakan dalam tempoh 60 hari mengikut perlembagaan."
    },
    {
        "is_top": False,
        "has_image": True,
        "img_url": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=600&q=80",
        "source": "星洲日報大北馬",
        "tag_zh": "文化傳媒", "tag_bm": "Media",
        "title_zh": "【文化傳媒】全國最後一份晚報退場！《光明日報》晚報10月31日出最後一期",
        "title_bm": "Edisi Petang Guang Ming Daily Tamat 31 Oktober, Catat Sejarah Akhbar Cetak",
        "excerpt_zh": "為紙本晚報寫下歷史句點！《光明日報》晚報宣布將於本月31日發行告別版，11月1日起全面停刊。",
        "excerpt_bm": "Akhbar petang terakhir di Malaysia, Guang Ming Daily menamatkan penerbitan fizikalnya pada 31 Oktober ini.",
        "content_zh": "【檳城訊】伴隨幾代北馬讀者夜間閱讀記憶的全國最後一份中文紙本晚報——《光明日報》晚報，正式發布讀者告別啟事。報社宣布將於2026年10月31日出版最後一期實體晚報，並自11月1日起全面終止在檳城、吉打及玻璃市等地的晚報發行業務。管理層指出，此舉是因應全媒體數碼化轉型的必然戰略調整，晨報與電子報將繼續正常運營，為傳統紙媒的「夜報時代」正式劃下圓滿句號。",
        "content_bm": "Guang Ming Daily mengumumkan edisi petang terakhir akan diterbitkan pada 31 Oktober 2026 berikutan transformasi digital pembaca, menamatkan legasi akhbar petang di utara tanah air."
    }
]

# 5. 生成新聞卡片
cards_html = ""
for idx, item in enumerate(news_items):
    card_id = "card_" + str(idx)
    top_class = "top-headline" if item["is_top"] else ""
    img_html = ""
    if item["has_image"]:
        img_html = (
            '<div class="news-img-box">'
            '<img src="' + item["img_url"] + '" alt="' + item["title_zh"] + '" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.style.display=\'none\';">'
            '<div class="source-stamp">'
            '<span>📷 來源：' + item["source"] + '</span>'
            '<button class="share-btn" onclick="shareNews(\'' + item["title_zh"] + '\')" title="分享">📤 分享</button>'
            '</div></div>'
        )
    cards_html += (
        '<article class="news-card ' + top_class + '">'
        + img_html +
        '<div class="card-inner">'
        '<div class="card-meta"><span class="news-tag" data-zh="' + item["tag_zh"] + '" data-bm="' + item["tag_bm"] + '">' + item["tag_zh"] + '</span></div>'
        '<h3 class="news-title" data-zh="' + item["title_zh"] + '" data-bm="' + item["title_bm"] + '">' + item["title_zh"] + '</h3>'
        '<p class="news-excerpt" data-zh="' + item["excerpt_zh"] + '" data-bm="' + item["excerpt_bm"] + '">' + item["excerpt_zh"] + '</p>'
        '<div class="full-content" id="' + card_id + '"><p data-zh="' + item["content_zh"] + '" data-bm="' + item["content_bm"] + '">' + item["content_zh"] + '</p></div>'
        '<button class="expand-btn" onclick="toggleExpand(\'' + card_id + '\', this)" data-zh="展開閱讀全文 ↓" data-bm="Baca Lanjut ↓">展開閱讀全文 ↓</button>'
        '</div></article>'
    )

# 6. 使用逐行拼接組裝 HTML，100% 免疫 Python 多行字串截斷
lines = [
    '<!DOCTYPE html>',
    '<html lang="zh-MY">',
    '<head>',
    '  <meta charset="UTF-8">',
    '  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">',
    '  <title>西門日報 | Berita Harian Simon</title>',
    '  <link rel="manifest" href="manifest.json">',
    '  <link rel="icon" type="image/svg+xml" href="icon.svg">',
    '  <link rel="apple-touch-icon" href="icon.svg">',
    '  <meta name="theme-color" content="#0f172a">',
    '  <meta name="mobile-web-app-capable" content="yes">',
    '  <meta name="apple-mobile-web-app-capable" content="yes">',
    '  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
    '  <meta name="apple-mobile-web-app-title" content="西門日報">',
    '  <style>',
    '    :root { --primary-red: #dc2626; --bg-body: #f8fafc; --card-bg: #ffffff; --border: #e2e8f0; --text: #0f172a; }',
    '    * { box-sizing: border-box; margin: 0; padding: 0; }',
    '    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif; background: var(--bg-body); color: var(--text); line-height: 1.5; padding-bottom: 30px; }',
    '    header { background: #ffffff; border-bottom: 3px solid var(--primary-red); position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }',
    '    .top-bar { max-width: 1100px; margin: 0 auto; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }',
    '    .logo-group h1 { font-size: 22px; font-weight: 900; color: var(--primary-red); letter-spacing: -0.5px; }',
    '    .actions { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }',
    '    .archive-select { padding: 5px 8px; font-size: 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: #f1f5f9; font-weight: 600; }',
    '    .install-btn { background: #0f172a; color: #38bdf8; border: 1px solid #38bdf8; padding: 5px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 3px; }',
    '    .lang-btn { background: var(--primary-red); color: white; border: none; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer; }',
    '    .container { max-width: 1100px; margin: 12px auto; padding: 0 10px; }',
    '    .news-grid { display: grid !important; grid-template-columns: repeat(2, 1fr) !important; gap: 10px !important; margin-bottom: 24px; }',
    '    .top-headline { grid-column: 1 / -1 !important; background: #fffdfd !important; border: 1.5px solid #f87171 !important; }',
    '    .news-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }',
    '    .news-img-box { position: relative; width: 100%; height: 125px; background: #e2e8f0; overflow: hidden; }',
    '    .top-headline .news-img-box { height: 180px; }',
    '    .news-img-box img { width: 100%; height: 100%; object-fit: cover; display: block; }',
    '    .source-stamp { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(15, 23, 42, 0.75); color: #ffffff; padding: 3px 8px; font-size: 10px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; backdrop-filter: blur(2px); }',
    '    .share-btn { background: #dc2626; color: #ffffff; border: none; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: 700; cursor: pointer; }',
    '    .card-inner { padding: 10px; display: flex; flex-direction: column; flex-grow: 1; }',
    '    .card-meta { margin-bottom: 4px; }',
    '    .news-tag { display: inline-block; font-size: 10px; font-weight: 800; color: #9a3412; background: #ffedd5; padding: 1px 5px; border-radius: 4px; }',
    '    .news-title { color: var(--primary-red) !important; font-size: 13px; line-height: 1.35; font-weight: 800; margin-bottom: 6px; }',
    '    .top-headline .news-title { font-size: 16px; }',
    '    .news-excerpt { font-size: 11px; color: #64748b; line-height: 1.45; margin-bottom: 8px; }',
    '    .full-content { display: none; font-size: 12px; color: #1e293b; line-height: 1.65; background: #f8fafc; padding: 10px; border-radius: 6px; border-top: 1px dashed #cbd5e1; margin-bottom: 8px; text-align: justify; }',
    '    .expand-btn { margin-top: auto; align-self: flex-start; background: none; border: 1px solid var(--primary-red); color: var(--primary-red); padding: 3px 8px; font-size: 11px; font-weight: 700; border-radius: 4px; cursor: pointer; }',
    '    .section-title { margin: 20px 0 10px 0; font-size: 15px; font-weight: 800; color: #0f172a; border-left: 4px solid var(--primary-red); padding-left: 8px; }',
    '    .events-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; margin-bottom: 24px; }',
    '    .event-card { background: #ffffff; border: 1px solid #cbd5e1; border-top: 3px solid #d97706; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; }',
    '    .event-date { font-size: 10px; font-weight: 800; color: #b45309; background: #fef3c7; padding: 2px 6px; border-radius: 4px; display: inline-block; margin-bottom: 6px; align-self: flex-start; }',
    '    .event-title { font-size: 13px; font-weight: 800; color: #1e293b; margin-bottom: 6px; }',
    '    .event-detail-box { display: none; font-size: 12px; color: #334155; line-height: 1.6; background: #fffbeb; padding: 8px; border-radius: 6px; border: 1px dashed #fcd34d; margin: 6px 0; }',
    '    .event-links { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }',
    '    .event-link-btn { font-size: 10px; font-weight: 700; padding: 3px 6px; border-radius: 4px; text-decoration: none; background: #f1f5f9; color: #0284c7; border: 1px solid #cbd5e1; }',
    '    .sponsor-card { background: #0f172a; color: #ffffff; border-radius: 8px; padding: 14px; margin-top: 10px; }',
    '    .sponsor-title { font-size: 15px; font-weight: 900; color: #38bdf8; margin-bottom: 4px; }',
    '    .sponsor-desc { font-size: 11px; color: #94a3b8; margin-bottom: 10px; }',
    '    .fleet-box { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px; font-size: 11px; color: #cbd5e1; margin-bottom: 10px; }',
    '    .contact-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; font-size: 11px; }',
    '    .wa-btn { margin-left: auto; background: #22c55e; color: #ffffff; padding: 5px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11px; }',
    '  </style>',
    '</head>',
    '<body>',
    '  <header>',
    '    <div class="top-bar">',
    '      <div class="logo-group"><h1 data-zh="西門日報" data-bm="Berita Harian Simon">西門日報</h1></div>',
    '      <div class="actions">',
    '        <select class="archive-select" id="archive-date"><option value="today">📅 今日：' + date_str + '</option><option value="yesterday">📅 昨天</option><option value="prev">📅 前天</option></select>',
    '        <button class="install-btn" id="installBtn" onclick="installPWA()"><span>📲 安裝APP</span></button>',
    '        <button class="lang-btn" onclick="toggleLanguage()"><span id="lang-text">Bahasa Melayu</span></button>',
    '      </div>',
    '    </div>',
    '  </header>',
    '  <main class="container">',
    '    <div class="section-title" data-zh="今日頭條與沙巴要聞" data-bm="Berita Utama & Sabah Hari Ini">今日頭條與沙巴要聞</div>',
    '    <div class="news-grid">' + cards_html + '</div>',
    '    <div class="section-title" data-zh="未來兩周至一個月 · 活動預告" data-bm="Acara & Ekspo Sabah (Akan Datang)">未來兩周至一個月 · 活動預告</div>',
    '    <div class="events-grid">',
    '      <div class="event-card">',
    '        <span class="event-date">11月13日 – 15日 · 亞庇 SICC</span>',
    '        <div class="event-title" data-zh="BIGSABAH Sale 2026 大型商貿展銷盛會" data-bm="Ekspo Jualan Mega BIGSABAH 2026">BIGSABAH Sale 2026 大型商貿展銷盛會</div>',
    '        <div class="event-detail-box" id="ev_1"><p data-zh="全州規模最大商業展銷盛會！全場設立超過650個品牌展位，涵蓋智能生活家電、沙巴在地製造優品、餐飲加盟招商以及跨國供應鏈展銷，預計帶動數百萬人次商貿對接。" data-bm="Ekspo jualan pengguna terbesar dengan 650 reruai merangkumi perkakas pintar, francais dan bekalan perniagaan.">全州規模最大商業展銷盛會！全場設立超過650個品牌展位，涵蓋智能生活家電、沙巴在地製造優品、餐飲加盟招商以及跨國供應鏈展銷，預計帶動數百萬人次商貿對接。</p><div class="event-links"><a class="event-link-btn" href="tel:088206000">📞 088-206000</a><a class="event-link-btn" href="https://wa.me/60168332118" target="_blank">💬 官方 WhatsApp</a></div></div>',
    '        <button class="expand-btn" onclick="toggleExpand(\'ev_1\', this)" data-zh="展開活動詳情 ↓" data-bm="Lihat Info ↓">展開活動詳情 ↓</button>',
    '      </div>',
    '      <div class="event-card">',
    '        <span class="event-date">11月20日 – 22日 · 亞庇 SICC 戶外展區</span>',
    '        <div class="event-title" data-zh="Borneo 4by4 越野與汽車文化節 (CULT)" data-bm="Festival Budaya Kereta & 4x4 Borneo">Borneo 4by4 越野與汽車文化節 (CULT)</div>',
    '        <div class="event-detail-box" id="ev_2"><p data-zh="匯聚全婆羅洲四驅越野改裝技術配件商、自駕遊露營配套方案及經典車型，提供品牌直營試駕及汽車後市場商業對接合作。" data-bm="Pameran aksesori 4x4, perkhemahan dan rangkaian perdagangan kenderaan lasak Borneo.">匯聚全婆羅洲四驅越野改裝技術配件商、自駕遊露營配套方案及經典車型，提供品牌直營試駕及汽車後市場商業對接合作。</p><div class="event-links"><a class="event-link-btn" href="tel:0198812399">📞 019-8812399 組委會</a></div></div>',
    '        <button class="expand-btn" onclick="toggleExpand(\'ev_2\', this)" data-zh="展開活動詳情 ↓" data-bm="Lihat Info ↓">展開活動詳情 ↓</button>',
    '      </div>',
    '      <div class="event-card">',
    '        <span class="event-date">11月29日 · 山打根市議會廣場</span>',
    '        <div class="event-title" data-zh="2026 依羅普拉慈善長跑與健康博覽會" data-bm="Larian Amal Elopura Sandakan 2026">2026 依羅普拉慈善長跑與健康博覽會</div>',
    '        <div class="event-detail-box" id="ev_3"><p data-zh="沙巴馬拉松系列賽收官站！全部參賽報名結餘款項將捐助山打根特殊兒童康復中心，設半馬、10KM及歡樂跑組別，期間舉辦為期3天的健康博覽會。" data-bm="Larian amal mengumpul dana kebajikan untuk kanak-kanak istimewa Sandakan dengan kategori 5KM & 10KM.">沙巴馬拉松系列賽收官站！全部參賽報名結餘款項將捐助山打根特殊兒童康復中心，設半馬、10KM及歡樂跑組別，期間舉辦為期3天的健康博覽會。</p><div class="event-links"><a class="event-link-btn" href="tel:089221144">📞 089-221144 籌委會</a><a class="event-link-btn" href="https://wa.me/60109301117" target="_blank">💬 報名諮詢</a></div></div>',
    '        <button class="expand-btn" onclick="toggleExpand(\'ev_3\', this)" data-zh="展開活動詳情 ↓" data-bm="Lihat Info ↓">展開活動詳情 ↓</button>',
    '      </div>',
    '    </div>',
    '    <footer class="sponsor-card">',
    '      <div class="sponsor-title" data-zh="MY CAR ENTERPRISE · 山打根租車與接送服務" data-bm="MY CAR ENTERPRISE · Sewa Kereta Sandakan">MY CAR ENTERPRISE · 山打根租車與接送服務</div>',
    '      <div class="sponsor-desc" data-zh="全車系齊全 · 自駕自遊 · 商務長租 · 機場專車接送" data-bm="Pandu Sendiri / Sewaan Korporat / Bersama Pemandu">全車系齊全 · 自駕自遊 · 商務長租 · 機場專車接送</div>',
    '      <div class="fleet-box"><div>• 掀背車：Myvi / Axia</div><div>• 舒適房車：Vios / Saga / Bezza</div><div>• 豪華商務：Vellfire / Alphard / Innova</div><div>• 客運越野：Van 11-12座 / Hilux 4x4</div></div>',
    '      <div class="contact-row"><span>負責人：<strong>Marco (010-9301117)</strong></span><span>微信：<strong>Thien1117</strong></span><a class="wa-btn" href="https://www.wasap.my/60109301117" target="_blank">WhatsApp 立即預約</a></div>',
    '    </footer>',
    '  </main>',
    '  <script>',
    '    if ("serviceWorker" in navigator) { window.addEventListener("load", function() { navigator.serviceWorker.register("sw.js").catch(function(err) { console.log(err); }); }); }',
    '    var currentLang = "zh";',
    '    function toggleExpand(id, btn) {',
    '      var el = document.getElementById(id);',
    '      var isVisible = el.style.display === "block";',
    '      el.style.display = isVisible ? "none" : "block";',
    '      var isEvent = id.indexOf("ev_") === 0;',
    '      if (isEvent) { btn.innerText = isVisible ? (currentLang === "zh" ? "展開活動詳情 ↓" : "Lihat Info ↓") : (currentLang === "zh" ? "收起活動詳情 ↑" : "Tutup Info ↑"); }',
    '      else { btn.innerText = isVisible ? (currentLang === "zh" ? "展開閱讀全文 ↓" : "Baca Lanjut ↓") : (currentLang === "zh" ? "收起全文 ↑" : "Tutup Bacaan ↑"); }',
    '    }',
    '    function toggleLanguage() {',
    '      currentLang = currentLang === "zh" ? "bm" : "zh";',
    '      document.getElementById("lang-text").innerText = currentLang === "zh" ? "Bahasa Melayu" : "中文版";',
    '      var installText = document.querySelector("#installBtn span");',
    '      if (installText) { installText.innerText = currentLang === "zh" ? "📲 安裝APP" : "📲 Pasang App"; }',
    '      document.querySelectorAll("[data-zh]").forEach(function(el) { var txt = el.getAttribute("data-" + currentLang); if (txt) el.innerText = txt; });',
    '    }',
    '    function shareNews(title) {',
    '      var shareData = { title: "《西門日報》", text: title + " - 詳情閱讀：" + window.location.href, url: window.location.href };',
    '      if (navigator.share) { navigator.share(shareData).catch(function(e) { console.log(e); }); }',
    '      else { navigator.clipboard.writeText(shareData.text); alert("新聞標題與鏈接已複製！可直接粘貼至 WhatsApp 或朋友圈分享。"); }',
    '    }',
    '    var deferredPrompt;',
    '    window.addEventListener("beforeinstallprompt", function(e) { e.preventDefault(); deferredPrompt = e; });',
    '    function installPWA() {',
    '      if (deferredPrompt) { deferredPrompt.prompt(); deferredPrompt.userChoice.then(function(choiceResult) { deferredPrompt = null; }); }',
    '      else {',
    '        var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;',
    '        if (isIOS) { alert("請點擊瀏覽器下方分享按鈕，滑動選擇【加入主畫面】安裝！"); }',
    '        else { alert("請點擊瀏覽器右上角選單（三個點），選擇【加到主畫面】或【安裝應用程式】！"); }',
    '      }',
    '    }',
    '  </script>',
    '</body>',
    '</html>'
]

full_html = "\n".join(lines)
with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("《西門日報》最新新聞庫已成功寫入 index.html！")
