import os
import json
import time
import datetime

my_tz = datetime.timezone(datetime.timedelta(hours=8))
now = datetime.datetime.now(my_tz)
date_str = now.strftime("%Y年%m月%d日")
weekday_map = {0:"星期一", 1:"星期二", 2:"星期三", 3:"星期四", 4:"星期五", 5:"星期六", 6:"星期日"}
weekday_str = weekday_map[now.weekday()]

# 深度精编版新闻库：带丰富内情长文、精选配图场景与来源角标
news_items = [
    {
        "is_top": True,
        "has_image": True,
        "source": "Sayang Sabah 官方通报",
        "svg": '<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg"><rect width="600" height="160" fill="#fee2e2"/><polygon points="200,130 280,40 360,130" fill="#94a3b8"/><rect x="80" y="60" width="100" height="70" rx="4" fill="#1e293b"/><rect x="95" y="75" width="70" height="25" rx="2" fill="#38bdf8"/><circle cx="480" cy="80" r="35" fill="#dc2626" opacity="0.85"/><path d="M465 80 L475 92 L500 68" stroke="#ffffff" stroke-width="5" fill="none" stroke-linecap="round"/></svg>',
        "tag_zh": "沙巴基建", "tag_bm": "Infrastruktur",
        "title_zh": "【沙巴基建】哈芝芝证实联邦开销达 71.78%，291项工程竣工交付",
        "title_bm": "KM: Prestasi Perbelanjaan Sabah Melonjak 71.78%, 291 Projek Siap",
        "excerpt_zh": "沙巴首长哈芝芝证实，沙巴联邦发展拨款支出已大幅提速至71.78%，全州291项重大民生基建竣工交付。",
        "excerpt_bm": "Ketua Menteri Sabah mengesahkan perbelanjaan persekutuan capai 71.78% dengan 291 projek siap sepenuhnya.",
        "content_zh": "【亚庇讯】沙巴首席部长拿督斯里哈芝芝诺昨日主持州发展行动委员会会议时透露，截至10月26日，沙巴在第12大马计划下的联邦发展开销表现大幅飙升至71.78%，较今年8月份的52.5%取得突破性进展。今年全州已顺利落成交付291项重大发展工程，重点项目涵盖亚庇科学中学迁建、兵南邦区多所国民型中小学校舍升级、内陆水利灌溉管网以及东海岸跨区支线公路。首长特别表扬州级监督专案组与联邦公共工程局（JKR）建立的每周现场巡检机制，成功挽救多项濒临搁置的“病态工程”，强调第四季将全力冲刺破八成支出大关，确保联邦资源全数转化为造福沙巴民生的实效资产。",
        "content_bm": "KM Datuk Seri Hajiji Noor mengesahkan pelaksanaan projek persekutuan di Sabah melonjak ke 71.78%. Sebanyak 291 projek telah disiapkan termasuk SM Sains Sabah dan menaik taraf sekolah di Penampang melalui pemantauan berkala JKR."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "ESSCOM 东安局发布",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#e0f2fe"/><path d="M0 80 Q 150 65, 300 80 L300 110 L0 110 Z" fill="#0284c7"/><rect x="80" y="45" width="70" height="25" rx="3" fill="#1e293b"/><polygon points="150,45 175,57 150,70" fill="#334155"/><circle cx="115" cy="38" r="6" fill="#dc2626"/></svg>',
        "tag_zh": "沙巴治安", "tag_bm": "Keselamatan",
        "title_zh": "【沙巴治安】ESSCOM 古纳海陆大突击扣10人，开罚及充公逾 26.9 万令吉",
        "title_bm": "Operasi Bersepadu ESSCOM di Kunak Tahan 10 Individu, Kompaun RM269k",
        "excerpt_zh": "东安局出动202名跨部门精锐在古纳展开海陆大围剿，截查走私黑点并严惩违规活动。",
        "excerpt_bm": "ESSCOM bersama 19 agensi menggerakkan 202 anggota dalam operasi bersepadu laut dan darat di Kunak.",
        "content_zh": "【古纳讯】沙巴东部特别保安指挥区（ESSCOM）统筹警方、海事执法机构、关税局及移民局等19个执法部门，于10月26日至27日连续48小时在古纳海域及沿海高风险红区展开“海上围剿”联合突击大行动。行动共动员202名执法官兵，全面封锁主要水上木屋区与私运航道。行动中依法拘留10名无法出示有效证件的涉案外籍人士及违法分子，起获多艘违规非法改装大马力快艇、违禁走私杂货以及非法渔具，累计开出复合罚单与查扣没收财物总估值高达26万9439令吉。指挥官强调，东安局将维持高压巡逻态势，严密阻截跨境渗透犯罪。",
        "content_bm": "Operasi bersepadu ESSZONE di Kunak melibatkan 202 anggota berjaya menahan 10 individu, merampas bot enjin kuasa tinggi serta pelbagai barangan penyeludupan bernilai RM269,439."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "砂拉越星洲日报 / 首相署",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#f0fdf4"/><rect x="70" y="25" width="60" height="60" rx="6" fill="#10b981"/><rect x="82" y="37" width="36" height="36" fill="#047857"/><circle cx="100" cy="55" r="8" fill="#a7f3d0"/><line x1="160" y1="40" x2="230" y2="40" stroke="#059669" stroke-width="3"/><line x1="160" y1="60" x2="210" y2="60" stroke="#059669" stroke-width="3"/></svg>',
        "tag_zh": "科技算力", "tag_bm": "Teknologi",
        "title_zh": "【科技算力】软银投资 2040 亿令吉，选中古晋与西马发展 AI 与绿色数据中心",
        "title_bm": "SoftBank Labur RM204b Bangun Pusat Data AI di Kuching & Semenanjung",
        "excerpt_zh": "孙正义对接安华敲定2040亿超大型外资，东马古晋依托丰富绿色水电跃升区域AI算力枢纽。",
        "excerpt_bm": "Masayoshi Son memuktamadkan pelaburan mega RM204 bilion bagi membina infrastruktur AI di Kuching.",
        "content_zh": "【吉隆坡讯】日本软银集团（SoftBank）创办人兼董事长孙正义日前与马来西亚首相拿督斯里安华举行线上高层闭门战略峰会，正式拍板高达2040亿令吉（约460亿美元）的巨额投资蓝图。软银集团将与大马本土主权基金携手，在东马砂拉越古晋以及西马南部黄金廊道，分别建设多座高能效绿色人工智能超级计算数据中心集群。古晋获选的主因在于婆罗洲具备充沛的水力与绿色清洁可再生能源，完全契合算力中心严苛的双碳环保标准。此举将推动东马加速转型为全东南亚算力基建核心，并在未来五年催生上万个前沿高科技数字岗位。",
        "content_bm": "Pelaburan gergasi RM204 bilion oleh SoftBank memilih Kuching berikutan bekalan tenaga hidro boleh diperbaharui yang stabil, sekali gus meletakkan Borneo sebagai hab pengkomputeran AI serantau."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "沙巴诗华日报 / PayNet",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#fefce8"/><rect x="80" y="15" width="50" height="80" rx="6" fill="#1e293b"/><rect x="85" y="23" width="40" height="60" rx="3" fill="#facc15"/><rect x="160" y="30" width="50" height="50" rx="4" fill="#0284c7"/><line x1="170" y1="45" x2="200" y2="45" stroke="#fff" stroke-width="3"/><line x1="170" y1="55" x2="195" y2="55" stroke="#fff" stroke-width="3"/></svg>',
        "tag_zh": "跨境金融", "tag_bm": "Kewangan",
        "title_zh": "【跨境金融】马银行 MAE 接入 Alipay+，免换汇扫码通中港韩菲老",
        "title_bm": "Maybank MAE Integrasi Alipay+, Imbas Kod QR di 5 Wilayah Serantau",
        "excerpt_zh": "大马人出国旅游免换外币，打开手机 MAE 应用直接扫码结算，畅行中港韩菲老五大目的地。",
        "excerpt_bm": "Pengguna Maybank kini boleh imbas kod QR di China, HK, Korea, Filipina dan Laos tanpa pertukaran wang.",
        "content_zh": "【金融专讯】马来西亚国家数字支付网络（PayNet）宣布与蚂蚁国际旗下的跨境支付解决方案 Alipay+ 达成跨国技术对接。马来亚银行（Maybank）作为首发阵营，已正式在其主力电子钱包 MAE 中全面开通双向跨境扫码服务。沙巴及全马用户即日起出境前往中国大陆、中国香港、韩国、菲律宾以及老挝等热门旅游及商贸目的地时，无需提前兑换外币纸钞或下载境外 App，只需打开 MAE 扫描带有 Alipay+ 标识的商家二维码，即可自动按实时最优惠汇率由马币户头即时扣款完成结算，消费体验全面看齐本地 DuitNow QR。",
        "content_bm": "Integrasi MAE dan Alipay+ membolehkan rakyat Malaysia membuat pembayaran kod QR di luar negara secara langsung dari akaun bank tempatan dengan kadar pertukaran mata wang yang telus dan kompetitif."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "沙巴星洲日报 / 财经专讯",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#eff6ff"/><line x1="90" y1="85" x2="90" y2="25" stroke="#0284c7" stroke-width="4"/><circle cx="90" cy="22" r="8" fill="#0284c7"/><line x1="170" y1="85" x2="170" y2="25" stroke="#ea580c" stroke-width="4"/><circle cx="170" cy="22" r="8" fill="#ea580c"/><path d="M90 40 Q 130 15, 170 40" stroke="#94a3b8" stroke-width="2" fill="none" stroke-dasharray="3,3"/></svg>',
        "tag_zh": "商业电信", "tag_bm": "Telekomunikasi",
        "title_zh": "【商业电信】明讯与 U Mobile 重启合并洽谈，拟打造全马最大电信集团",
        "title_bm": "Maxis & U Mobile Sambung Semula Rundingan Penggabungan Terbesar",
        "excerpt_zh": "大马电讯业再掀并购风云，明讯与U Mobile展开股权架构重组磋商，若合拢将统领超2400万用户。",
        "excerpt_bm": "Maxis dan U Mobile dilaporkan memulakan kembali rundingan penggabungan untuk menguasai pasaran 5G.",
        "content_zh": "【吉隆坡财经讯】来自马来西亚投行圈权威信源透露，国内两大移动网络运营商——明讯（Maxis Bhd）与 U Mobile Sdn Bhd 大股东已正式重返谈判桌，针对两家公司的战略性业务整合与换股合并方案展开深入尽职调查。若该超级并购案最终成形，新合并体将坐拥超过 2400 万名活跃移动通信及宽带用户，一举超越合并后的天地通数码网络（CelcomDigi），跃居全马市场份额第一的电信巨无霸。分析师指出，合并的核心动力在于整合双方庞大的频谱资源与基站站址，分摊沙巴、砂拉越内陆第二 5G 网络的巨额资本开销，提升网络覆盖质量。",
        "content_bm": "Penggabungan gergasi Maxis dan U Mobile dijangka menghasilkan syarikat telekomunikasi terbesar di Malaysia dengan lebih 24 juta pengguna, sekali gus mempercepat liputan rangkaian 5G di Sabah dan Sarawak."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "LHDN 内陆税收局公函",
        "tag_zh": "政府防骗", "tag_bm": "Amaran",
        "title_zh": "【政府防骗】LHDN 发紧急警示：警惕冒名伪造邮件骗取个人文件",
        "title_bm": "LHDN Keluar Amaran: Waspada Emel Palsu Tuntut Dokumen Peribadi",
        "excerpt_zh": "税收局警告出现钓鱼邮件伪称“退税稽核”，诱导纳税人点击恶意附件，官方重申绝不通过个人电邮索资。",
        "excerpt_bm": "LHDN menasihati orang ramai agar tidak membuka e-mel palsu yang meminta pengesahan maklumat cukai.",
        "content_zh": "【布城讯】内陆税收局（LHDN）今日发布最高级别防诈骗通告，警示近期有跨国网络钓鱼犯罪团伙大肆伪造该局官方抬头与公函印章，向纳税公众发送以“2026退税核实通知”或“最后补税稽核”为主题的诈骗电子邮件。邮件内诱导纳税人点击恶意下载链接或填报带有木马的压缩包附件，企图截获纳税人的银行个人网银账号、身份证信息及商业财务报表。税收局郑重澄清，所有官方税务审核或退款通知均严格通过 MyTax 官方安全加密门户下发，绝不会使用未经认证的个人邮箱直接索取机密，民众接获可疑邮件应即刻向当局热线检举核实。",
        "content_bm": "LHDN menegaskan semua urusan cukai rasmi hanya disalurkan melalui portal selamat MyTax dan orang ramai diminta tidak menekan pautan atau memuat turun lampiran daripada emel yang meragukan."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "财政部 / 关爱基本金专网",
        "tag_zh": "民生福利", "tag_bm": "Bantuan",
        "title_zh": "【民生福利】2027 STR 援助金审核收紧，有车有房等 8 种情况恐遭拒批",
        "title_bm": "Semakan STR 2027 Diperketat: 8 Kriteria Pemilikan Boleh Ditolak",
        "excerpt_zh": "财政部全面打通20个部门大数据交叉比对，拥有大排量豪车、公司盈利或海外资产者将丧失领款资格。",
        "excerpt_bm": "Kementerian Kewangan mengetatkan syarat kelayakan STR melalui integrasi data pelbagai agensi.",
        "content_zh": "【财政要闻】财政部常务副部长在国会明确指出，为杜绝“富人骗领穷人福利”的不公现象，针对2027年度爱心援助金（STR）的资格审查体系将迎来史上最严的大数据跨机构交叉验证。税收局将无缝联动陆路交通局（JPJ）、国民登记局、公司委员会（SSM）以及土地局等20个核心数据库。凡申请者或其配偶名下存在以下情况将被系统自动驳回：包括名下拥有排气量高于2000cc的非商业豪华私家车、名下注册有正常盈利分红的合伙企业、拥有两处以上商业地产估值超标、月度频繁大额跨境结汇等八类资产红线，确保国家有限的公帑100%精准投向真正的赤贫与低收入家庭。",
        "content_bm": "Kriteria kelayakan STR akan disaring ketat menggunakan pangkalan data JPJ dan SSM. Pemilikan kenderaan mewah atau syarikat berdaftar aktif akan menyebabkan permohonan bantuan ditolak secara automatik."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "教育部 KPM 官方通告",
        "tag_zh": "学校假期", "tag_bm": "Pendidikan",
        "title_zh": "【学校假期】教育部官宣屠妖节假期：除砂拉越外全马中小学师生连休 4 天",
        "title_bm": "KPM Sahkan Cuti Berganti Deepavali: Sekolah Bercuti 4 Hari Kecuali Sarawak",
        "excerpt_zh": "教育部下发官方节庆校历公函，全马除砂州外均享有4天连假，东马飞往西马返乡机票全面紧俏。",
        "excerpt_bm": "KPM mengesahkan cuti empat hari sempena perayaan Deepavali untuk semua negeri kecuali Sarawak.",
        "content_zh": "【吉隆坡教育讯】教育部（KPM）正式向全马各州教育局发布节庆特别调休备忘录。根据全国校历统一安排，除砂拉越州未将屠妖节列为主流法定连休日之外，沙巴、吉隆坡以及西马各州的所有源流中小学师生，将在屠妖节正日期间享有为期4天（周五至周一）的连贯长假期。该项公函不仅为广大印度裔教职员和家庭提供了充足的祈福与探亲时间，也带动了跨州文旅出行热潮。沙巴亚庇及山打根往返吉隆坡、槟城的国内骨干航线连日来机票订座率突破92%，大马民航局与各州交警已全面启动节庆道路保畅疏导方案。",
        "content_bm": "Kementerian Pendidikan mengumumkan cuti berganti empat hari sempena Deepavali bagi sekolah di Sabah dan Semenanjung, membolehkan warga pendidik dan pelajar menikmati percutian panjang."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "大马气象局 MetMalaysia",
        "tag_zh": "天气警报", "tag_bm": "Cuaca",
        "title_zh": "【天气警报】东北季候风来袭，气象局预测 5 次长命雨恐致多州水灾",
        "title_bm": "Monsun Timur Laut Bermula: MetMalaysia Ramal 5 Episod Hujan Berterusan",
        "excerpt_zh": "气象局示警季候风正式吹袭，沙巴沿海与东海岸内陆面临密集持续降雨，低洼村民须防范突发泥石流。",
        "excerpt_bm": "Jabatan Meteorologi Malaysia meramalkan episod hujan lebat berterusan yang berisiko mengakibatkan banjir kilat.",
        "content_zh": "【气象防汛讯】马来西亚气象局（MetMalaysia）发布全国灾害气候预警，证实一年一度的东北季候风已于10月27日起正式活跃并逐步加强，预料将持续肆虐至明年3月上旬。气象监测模型显示，季风期间全马尤其是沙巴东海岸（包括山打根、拿笃、仙本那、古达）以及半岛东海岸将至少经历5波高强度的长命持续暴雨过程。连日积水配合大潮汐现象，极易在山脚沿溪及低洼居住区诱发城市内涝与严重山体滑坡。国家天灾管理机构（NADMA）已指示沙巴各地方灾害委员会全员进入二级待命状态，疏散中心物资与救生艇已全数部署到位。",
        "content_bm": "MetMalaysia memberi amaran Monsun Timur Laut dijangka membawa sekurang-kurangnya 5 episod hujan lebat berterusan yang boleh menyebabkan bencana banjir di kawasan pantai timur Sabah."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "星洲日报 / 在地商业动态",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#fef2f2"/><ellipse cx="150" cy="55" rx="45" ry="30" fill="#fee2e2" stroke="#dc2626" stroke-width="2"/><circle cx="150" cy="55" r="22" fill="#78350f"/><path d="M140 30 Q 150 15, 160 30" stroke="#f87171" stroke-width="2" fill="none"/></svg>',
        "tag_zh": "商业焦点", "tag_bm": "Perniagaan",
        "title_zh": "【商业焦点】华阳茶室吉打新店推三语菜单迎客现场大排长龙",
        "title_bm": "Oriental Kopi Buka Cawangan Kedah: Menu Tiga Bahasa Tarik Tumpuan",
        "excerpt_zh": "华阳茶室进军吉打首开门市，全面推行国文、中文与英文三语菜单，化解语言误会现场客似云来。",
        "excerpt_bm": "Oriental Kopi memperkenalkan menu tiga bahasa di cawangan terbaharunya di Kedah dan mendapat sambutan hangat.",
        "content_zh": "【吉打亚罗士打讯】此前因菜单语言标注而在社交媒体引发广泛舆论热议的知名连锁餐饮品牌“华阳茶室”（Oriental Kopi），昨日正式在吉打州开设其北部首间旗舰分店。令人瞩目的是，管理层吸取了此前的公众关切，在新门市全面启用高规格的马来文、中文及英文三语对照点餐系统与实体菜单，所有招牌菜品均清晰罗列主要食材源头与清真认证供应链来源。这一兼顾包容与多元文化的务实举措迅速赢得了不同族群食客的好评，开业当天清晨便吸引大批本地市民在店外大排长龙品尝招牌蛋挞与浓郁白咖啡，化解争议并树立了跨族群商业经营的积极范式。",
        "content_bm": "Oriental Kopi merasmikan cawangan baharu di Kedah dengan memperkenalkan menu lengkap tiga bahasa, meredakan kebimbangan masyarakat dan menarik kehadiran ramai pengunjung tempatan."
    },
    {
        "is_top": False,
        "has_image": False,
        "source": "卫生部 KKM 官方公告",
        "tag_zh": "公共卫生", "tag_bm": "Kesihatan",
        "title_zh": "【公共卫生】卫生部推 MyLapor 官方功能，通过 MySejahtera 检举违规抽烟",
        "title_bm": "KKM Lancar MyLapor: Aduan Merokok Dilarang Melalui MySejahtera",
        "excerpt_zh": "卫生部赋予民众数字监督权，手机拍下违规吸烟照片一键上传，卫生执法官员将在24小时内到场查处。",
        "excerpt_bm": "KKM melancarkan ciri MyLapor dalam aplikasi MySejahtera bagi memudahkan aduan premis merokok secara terus.",
        "content_zh": "【布城卫生讯】卫生部长宣布在国民级应用 MySejahtera 中全面上线全新公众卫生监督模块“MyLapor”。新功能专为严打餐馆、冷气咖啡厅及公共游乐场非法违规抽烟行为而设。公众如在冷气餐厅或禁止吸烟法定区域目击违例吸烟或电子烟行为，只需打开 MySejahtera 的 MyLapor 页面，实时拍照存证、自动定位事发商户地址并提交举报。卫生部中央指挥中心收到案件后将自动分派至各县区卫生执法组，执法官将依照《2024年公共卫生吸烟产品管制法》在规定时限内突击现场开出至少250令吉的复合罚单，打造无烟清新的就餐环境。",
        "content_bm": "Kementerian Kesihatan memperkenalkan modul MyLapor di MySejahtera untuk membolehkan orang ramai merakam gambar dan melaporkan pesalah merokok di premis makanan secara terus kepada penguat kuasa."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "槟城警方官方通告",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#fef2f2"/><rect x="80" y="45" width="90" height="35" rx="4" fill="#dc2626"/><circle cx="105" cy="80" r="10" fill="#1e293b"/><circle cx="150" cy="80" r="10" fill="#1e293b"/><rect x="110" y="32" width="20" height="13" fill="#3b82f6"/><circle cx="120" cy="25" r="5" fill="#ef4444"/></svg>',
        "tag_zh": "法治严打", "tag_bm": "Jenayah",
        "title_zh": "【法治严打】槟警拘捕擅自驾驶贴山寨“Bomba”消拯车标的私家车司机",
        "title_bm": "Polis Tahan Pemandu Kereta Pasang Pelekat & Siren Bomba Palsu",
        "excerpt_zh": "私家车擅自贴上消拯局官方标志并装配警示灯在公路招摇，槟城交警根据民众行车记录仪迅速破案抓人。",
        "excerpt_bm": "Polis Pulau Pinang menahan seorang lelaki yang menyamar menggunakan kenderaan berperekat Jabatan Bomba palsu.",
        "content_zh": "【乔治市讯】针对日前在社交短视频平台疯传的“山寨消拯局私家车闯红灯”案件，槟城总警长证实警方已于前夜在威中区成功逮捕涉案的38岁本地男司机，并当场依法查扣其名下的一辆红色本田私家车。经警方仔细搜查，该轿车不仅在车门及引擎盖上全套仿冒贴上大马消拯局（Bomba）的法定徽章与反光条，车顶更私自改装加装了高分贝警报蜂鸣器及频闪爆闪灯，涉嫌在公路上滥用特权逼迫其他守法车辆让道。全案目前已援引《刑事法典》第170条文（冒充公务员）及《1987年陆路交通法令》展开全方位刑事调查，罪成可判处长期监禁与巨额罚款。",
        "content_bm": "Polis Pulau Pinang bertindak pantas menahan pemandu kereta yang tular kerana memasang pelekat rasmi Jabatan Bomba dan siren kecemasan secara haram untuk mengelirukan pengguna jalan raya."
    },
    {
        "is_top": False,
        "has_image": True,
        "source": "Kupikupifm / Sazarice 官方",
        "svg": '<svg viewBox="0 0 300 110" xmlns="http://www.w3.org/2000/svg"><rect width="300" height="110" fill="#fdf4ff"/><circle cx="100" cy="55" r="30" fill="#c084fc"/><circle cx="100" cy="55" r="22" fill="#7e22ce"/><path d="M150 40 L210 40 L195 70 L150 70 Z" fill="#ec4899"/><circle cx="230" cy="55" r="10" fill="#f43f5e"/></svg>',
        "tag_zh": "沙巴生活", "tag_bm": "Gaya Hidup",
        "title_zh": "【沙巴生活】Sazarice 联手 Kupikupifm 展开《Jom Cari Momom》探寻亚庇美食",
        "title_bm": "Sazarice Bersama Kupikupifm Cari Momom Terpaling Mantap di KK",
        "excerpt_zh": "沙巴在地电台主持人 Felix 与 Ojoe 现身亚庇街头，带着民众探寻平价大碗的地道沙巴小吃与香米饭店。",
        "excerpt_bm": "Program Jom Cari Momom bersama Kupikupifm menjelajah gerai makan menarik di sekitar Kota Kinabalu.",
        "content_zh": "【亚庇生活志】沙巴家喻户晓的知名米粮品牌 Sazarice 宣布与本土高人气电台 Kupikupifm 联合出品的在地美食文化微综艺《Jom Cari Momom》第5集正式全网开播。本集由当红主持搭档 Felix 和 Ojoe 联袂出镜，两位主持人开着采风车走街串巷，深入亚庇市中心下南南以及哥隆邦的老牌茶餐室与平民大排档。节目以生动幽默的沙巴地道马来语方言，向全州观众大篇幅推介采用优质本地香米焖煮的砂煲鸡饭、秘制生肉面以及传统牛杂粉。节目播出后好评如潮，不仅带旺了受访老店的堂食人气，更引发全州年轻网友热烈留言互动打卡。",
        "content_bm": "Program santai Jom Cari Momom yang diterbitkan oleh Sazarice bersama penyampai Kupikupifm mengetengahkan keunikan makanan tempatan Sabah di sekitar Penampang dan Kota Kinabalu."
    }
]

# 组装卡片 HTML
cards_html = ""
for idx, item in enumerate(news_items):
    card_id = f"card_{idx}"
    is_top = item["is_top"]
    top_class = "top-headline" if is_top else ""
    
    # 图片与来源角标渲染
    img_html = ""
    if item["has_image"]:
        img_html = f"""
        <div class="news-img-box">
          {item['svg']}
          <div class="source-stamp">
            <span>📷 来源：{item['source']}</span>
            <button class="share-btn" onclick="shareNews('{item['title_zh']}')" title="分享到微信/WhatsApp">📤 分享</button>
          </div>
        </div>
        """
    
    cards_html += f"""
    <article class="news-card {top_class}">
      {img_html}
      <div class="card-inner">
        <div class="card-meta">
          <span class="news-tag" data-zh="{item['tag_zh']}" data-bm="{item['tag_bm']}">{item['tag_zh']}</span>
        </div>
        <h3 class="news-title" data-zh="{item['title_zh']}" data-bm="{item['title_bm']}">{item['title_zh']}</h3>
        <p class="news-excerpt" data-zh="{item['excerpt_zh']}" data-bm="{item['excerpt_bm']}">{item['excerpt_zh']}</p>
        <div class="full-content" id="{card_id}">
          <p data-zh="{item['content_zh']}" data-bm="{item['content_bm']}">{item['content_zh']}</p>
        </div>
        <button class="expand-btn" onclick="toggleExpand('{card_id}', this)" data-zh="展开阅读全文 ↓" data-bm="Baca Lanjut ↓">展开阅读全文 ↓</button>
      </div>
    </article>
    """

full_html = f"""<!DOCTYPE html>
<html lang="zh-MY">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>西门日报 | Berita Harian Simon</title>
  <style>
    :root {{
      --primary-red: #dc2626;
      --bg-body: #f8fafc;
      --card-bg: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
      background: var(--bg-body);
      color: var(--text);
      line-height: 1.5;
      padding-bottom: 30px;
    }}
    header {{
      background: #ffffff;
      border-bottom: 3px solid var(--primary-red);
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .top-bar {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 10px 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .logo-group h1 {{
      font-size: 22px;
      font-weight: 900;
      color: var(--primary-red);
      letter-spacing: -0.5px;
    }}
    .actions {{ display: flex; align-items: center; gap: 8px; }}
    .archive-select {{
      padding: 5px 8px;
      font-size: 12px;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      background: #f1f5f9;
      font-weight: 600;
    }}
    .lang-btn {{
      background: var(--primary-red);
      color: white;
      border: none;
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .container {{
      max-width: 1100px;
      margin: 12px auto;
      padding: 0 10px;
    }}
    
    /* 核心排版：手机与电脑端全量双列多宫格 */
    .news-grid {{
      display: grid !important;
      grid-template-columns: repeat(2, 1fr) !important;
      gap: 10px !important;
      margin-bottom: 24px;
    }}
    
    /* 第一条全宽大头条 */
    .top-headline {{
      grid-column: 1 / -1 !important;
      background: #fffdfd !important;
      border: 1.5px solid #f87171 !important;
    }}
    
    .news-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }}
    
    /* 图片与底部来源印记 */
    .news-img-box {{
      position: relative;
      width: 100%;
      height: 110px;
      background: #f1f5f9;
      border-bottom: 1px solid #e2e8f0;
    }}
    .top-headline .news-img-box {{
      height: 150px;
    }}
    .news-img-box svg {{
      width: 100%;
      height: 100%;
      display: block;
    }}
    .source-stamp {{
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(15, 23, 42, 0.75);
      color: #ffffff;
      padding: 3px 8px;
      font-size: 10px;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
      backdrop-filter: blur(2px);
    }}
    .share-btn {{
      background: #dc2626;
      color: #ffffff;
      border: none;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
    }}
    
    .card-inner {{
      padding: 10px;
      display: flex;
      flex-direction: column;
      flex-grow: 1;
    }}
    
    .card-meta {{ margin-bottom: 4px; }}
    .news-tag {{
      display: inline-block;
      font-size: 10px;
      font-weight: 800;
      color: #9a3412;
      background: #ffedd5;
      padding: 1px 5px;
      border-radius: 4px;
    }}
    .news-title {{
      color: var(--primary-red) !important;
      font-size: 13px;
      line-height: 1.35;
      font-weight: 800;
      margin-bottom: 6px;
    }}
    .top-headline .news-title {{
      font-size: 16px;
    }}
    .news-excerpt {{
      font-size: 11px;
      color: #64748b;
      line-height: 1.45;
      margin-bottom: 8px;
    }}
    
    /* 展开全文丰富内容区域 */
    .full-content {{
      display: none;
      font-size: 12px;
      color: #1e293b;
      line-height: 1.65;
      background: #f8fafc;
      padding: 10px;
      border-radius: 6px;
      border-top: 1px dashed #cbd5e1;
      margin-bottom: 8px;
      text-align: justify;
    }}
    .expand-btn {{
      margin-top: auto;
      align-self: flex-start;
      background: none;
      border: 1px solid var(--primary-red);
      color: var(--primary-red);
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 4px;
      cursor: pointer;
    }}
    
    /* 活动专区 */
    .section-title {{
      margin: 20px 0 10px 0;
      font-size: 15px;
      font-weight: 800;
      color: #0f172a;
      border-left: 4px solid var(--primary-red);
      padding-left: 8px;
    }}
    .events-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      margin-bottom: 24px;
    }}
    .event-card {{
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-top: 3px solid #d97706;
      border-radius: 8px;
      padding: 12px;
    }}
    .event-date {{
      font-size: 10px;
      font-weight: 800;
      color: #b45309;
      background: #fef3c7;
      padding: 2px 6px;
      border-radius: 4px;
      display: inline-block;
      margin-bottom: 6px;
    }}
    .event-title {{
      font-size: 13px;
      font-weight: 800;
      color: #1e293b;
      margin-bottom: 4px;
    }}
    .event-desc {{
      font-size: 11px;
      color: #64748b;
      margin-bottom: 8px;
    }}
    .event-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .event-link-btn {{
      font-size: 10px;
      font-weight: 700;
      padding: 3px 6px;
      border-radius: 4px;
      text-decoration: none;
      background: #f1f5f9;
      color: #0284c7;
      border: 1px solid #cbd5e1;
    }}
    
    /* 置底商业广告 */
    .sponsor-card {{
      background: #0f172a;
      color: #ffffff;
      border-radius: 8px;
      padding: 14px;
      margin-top: 10px;
    }}
    .sponsor-title {{
      font-size: 15px;
      font-weight: 900;
      color: #38bdf8;
      margin-bottom: 4px;
    }}
    .sponsor-desc {{
      font-size: 11px;
      color: #94a3b8;
      margin-bottom: 10px;
    }}
    .fleet-box {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 4px;
      font-size: 11px;
      color: #cbd5e1;
      margin-bottom: 10px;
    }}
    .contact-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      font-size: 11px;
    }}
    .wa-btn {{
      margin-left: auto;
      background: #22c55e;
      color: #ffffff;
      padding: 5px 12px;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 700;
      font-size: 11px;
    }}
  </style>
</head>
<body>
  <header>
    <div class="top-bar">
      <div class="logo-group">
        <h1 data-zh="西门日报" data-bm="Berita Harian Simon">西门日报</h1>
      </div>
      <div class="actions">
        <select class="archive-select" id="archive-date">
          <option value="today">📅 今日：{date_str}</option>
          <option value="yesterday">📅 昨天</option>
          <option value="prev">📅 前天</option>
        </select>
        <button class="lang-btn" onclick="toggleLanguage()">
          <span id="lang-text">Bahasa Melayu</span>
        </button>
      </div>
    </div>
  </header>

  <main class="container">
    <div class="section-title" data-zh="今日头条与沙巴要闻" data-bm="Berita Utama & Sabah Hari Ini">今日头条与沙巴要闻</div>
    
    <div class="news-grid">
      {cards_html}
    </div>

    <div class="section-title" data-zh="未来两周至一个月 · 活动预告" data-bm="Acara & Ekspo Sabah (Akan Datang)">未来两周至一个月 · 活动预告</div>
    <div class="events-grid">
      <div class="event-card">
        <span class="event-date">11月13日 – 15日 · 亚庇 SICC</span>
        <div class="event-title" data-zh="BIGSABAH Sale 2026 大型商贸展销盛会" data-bm="Ekspo Jualan Mega BIGSABAH 2026">BIGSABAH Sale 2026 大型商贸展销盛会</div>
        <p class="event-desc" data-zh="全州规模最大商业展销，逾650个品牌展位涵盖智能家电、在地制造、零售加盟与采购对接。" data-bm="Ekspo jualan pengguna terbesar di SICC merangkumi 650 reruai perniagaan.">全州规模最大商业展销，逾650个品牌展位涵盖智能家电、在地制造、零售加盟与采购对接。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:088206000">📞 088-206000</a>
          <a class="event-link-btn" href="https://wa.me/60168332118" target="_blank">💬 WhatsApp 咨询</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月20日 – 22日 · 亚庇 SICC 户外展区</span>
        <div class="event-title" data-zh="Borneo 4by4 越野与汽车文化节 (CULT)" data-bm="Festival Budaya Kereta & 4x4 Borneo">Borneo 4by4 越野与汽车文化节 (CULT)</div>
        <p class="event-desc" data-zh="婆罗洲四驱改装零件展销、自驾露营装备与汽车后市场企业合作平台。" data-bm="Pameran aksesori 4x4 dan perkhemahan ekstrem serantau Borneo.">婆罗洲四驱改装零件展销、自驾露营装备与汽车后市场企业合作平台。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:0198812399">📞 019-8812399</a>
        </div>
      </div>
      <div class="event-card">
        <span class="event-date">11月29日 · 山打根市议会广场</span>
        <div class="event-title" data-zh="2026 依罗普拉慈善长跑与健康博览会" data-bm="Larian Amal Elopura Sandakan 2026">2026 依罗普拉慈善长跑与健康博览会</div>
        <p class="event-desc" data-zh="为山打根特殊儿童康复中心筹集善款，设立半马、10KM与欢乐跑，配套3天健康博览会。" data-bm="Larian amal mengumpul dana kebajikan untuk kanak-kanak istimewa Sandakan.">为山打根特殊儿童康复中心筹集善款，设立半马、10KM与欢乐跑，配套3天健康博览会。</p>
        <div class="event-links">
          <a class="event-link-btn" href="tel:089221144">📞 089-221144</a>
          <a class="event-link-btn" href="https://wa.me/60109301117" target="_blank">💬 报名咨询</a>
        </div>
      </div>
    </div>

    <footer class="sponsor-card">
      <div class="sponsor-title" data-zh="MY CAR ENTERPRISE · 山打根租车与接送服务" data-bm="MY CAR ENTERPRISE · Sewa Kereta Sandakan">MY CAR ENTERPRISE · 山打根租车与接送服务</div>
      <div class="sponsor-desc" data-zh="全车系齐全 · 自驾自游 · 商务长租 · 机场专车接送" data-bm="Pandu Sendiri / Sewaan Korporat / Bersama Pemandu">全车系齐全 · 自驾自游 · 商务长租 · 机场专车接送</div>
      <div class="fleet-box">
        <div>• 掀背车：Myvi / Axia</div>
        <div>• 舒适房车：Vios / Saga / Bezza</div>
        <div>• 豪华商务：Vellfire / Alphard / Innova</div>
        <div>• 客运越野：Van 11-12座 / Hilux 4x4</div>
      </div>
      <div class="contact-row">
        <span>负责人：<strong>Marco (010-9301117)</strong></span>
        <span>微信：<strong>Thien1117</strong></span>
        <a class="wa-btn" href="https://www.wasap.my/60109301117" target="_blank">WhatsApp 立即预约</a>
      </div>
    </footer>
  </main>

  <script>
    let currentLang = 'zh';
    function toggleExpand(id, btn) {{
      const el = document.getElementById(id);
      const isVisible = el.style.display === 'block';
      el.style.display = isVisible ? 'none' : 'block';
      btn.innerText = isVisible 
        ? (currentLang === 'zh' ? '展开阅读全文 ↓' : 'Baca Lanjut ↓')
        : (currentLang === 'zh' ? '收起全文 ↑' : 'Tutup Bacaan ↑');
    }}
    function toggleLanguage() {{
      currentLang = currentLang === 'zh' ? 'bm' : 'zh';
      document.getElementById('lang-text').innerText = currentLang === 'zh' ? 'Bahasa Melayu' : '中文版';
      document.querySelectorAll('[data-zh]').forEach(el => {{
        const txt = el.getAttribute(`data-${{currentLang}}`);
        if (txt) el.innerText = txt;
      }});
    }}
    function shareNews(title) {{
      const shareData = {{
        title: '《西门日报》',
        text: title + ' - 详情阅读：' + window.location.href,
        url: window.location.href
      }};
      if (navigator.share) {{
        navigator.share(shareData).catch((e) => console.log(e));
      }} else {{
        navigator.clipboard.writeText(shareData.text);
        alert('新闻标题与链接已复制！可直接粘贴至 WhatsApp 或朋友圈分享。');
      }}
    }}
  </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(full_html)

print("《西门日报》精选配图+来源角标+深度长文完整版已成功写入 index.html！")
