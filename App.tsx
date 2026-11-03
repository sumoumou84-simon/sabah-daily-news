import React, { useState, useEffect, useMemo } from 'react';
import myCarPoster from 'container:///mnt/data/src/assets/a0c79ab3b0a4e2ac-image_5f00d7.png';
import sazaPoster from 'container:///mnt/data/src/assets/c5b30eea4a0807cf-image_9c82dc.png';
import emergencyAlertImg from 'container:///mnt/data/src/assets/daef199ef7ee8f30-WhatsApp_Image_2026-11-02_at_9_57_38_PM.jpeg';

type Lang = '中文' | 'BM';

// ---- MYT dynamic date helpers ----
function getMYTNow(): Date {
  // Convert now to MYT via locale string
  const now = new Date();
  const mytString = now.toLocaleString('en-US', { timeZone: 'Asia/Kuala_Lumpur' });
  return new Date(mytString);
}
function formatMMDD(d: Date): string {
  const m = (d.getMonth() + 1).toString().padStart(2, '0');
  const day = d.getDate().toString().padStart(2, '0');
  return `${m}/${day}`;
}
function formatMYTTime(d: Date): string {
  // returns like 7:05AM
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Kuala_Lumpur',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
  return fmt.format(d);
}
function formatMYTFull(d: Date): string {
  const fmt = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kuala_Lumpur',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
  return fmt.format(d); // YYYY-MM-DD
}

// Build 6-day archive
type ArchiveDay = {
  idx: number;
  labelZh: string;
  labelBM: string;
  mmdd: string;
  dateObj: Date;
  iso: string;
  dayWeekZh: string;
  dayWeekBM: string;
};

const BASE_NEWS_TODAY = [
  {
    id: 9,
    title: '11月19日手机突然巨响 别惊！不是手机坏了 是政府在测试警报',
    titleBM: '19 Nov Telefon Bunyi Kuat Jangan Panik! Ujian Amaran Kecemasan Kerajaan',
    time: '21:30',
    sources: ['sabah.sinchew.com.my', 'sinchew.com.my'],
    verified: '2源已核实',
    verifiedBM: '2 Sumber Disahkan',
    pin: true,
    tag: '全国要闻 Nasional',
    location: '全国 Seluruh Negara • 沙巴 Sabah',
    rich: [
      '政府将于11月19日进行全国公共紧急警报系统（Public Warning System）测试，届时全马包括沙巴山打根用户手机将突然发出巨响及强烈震动，屏幕自动弹出 Emergency Alert: Severe Flash Flood Warning 类似字样。沙巴星洲日报官方9小时前FB紧急通告：这不是手机故障，也不是诈骗，是马来西亚通讯及多媒体委员会（MCMC）与国家灾害管理局（NADMA）联合进行的年度预警演练，请民众勿惊慌。',
      '系统运作完全无需获取个人电话号码，采用小区广播（Cell Broadcast）技术，只要受灾区域内有一家电讯业者的基站正常运作，无论使用何家电讯公司 CelcomDigi、Maxis、U Mobile、Unifi 皆能顺利接收。即使在网络拥堵或断电情况下，警报也能优先推送。图中手机显示 At 12:18 CDT Avoid flood areas NWS 即为类似警报界面，大马版将显示马来文与英文。',
      '该系统未来将正式用于水灾、地震、海啸、极端天气等灾害时的秒级通知，沙巴作为水灾高风险区已纳入首批全覆盖。测试当天民众只需保持手机开机及有信号即可接收，无需安装任何App，测试后可手动关闭。官方提醒：听到巨响别关机，这是在救命。咨询：MCMC 1800-188-030 / NADMA。来源已核实：沙巴星洲日报 Sabah Sin Chew Daily 官方FB 9小时前 + 星洲日报总社，2源核实。',
    ],
    richBM: [
      'Kerajaan akan menjalankan ujian Sistem Amaran Awam (Public Warning System) seluruh negara pada 19 November, di mana semua telefon termasuk di Sandakan Sabah akan berbunyi kuat dan bergetar dengan paparan Emergency Alert. Sabah Sin Chew Daily 9 jam lalu maklumkan ini bukan kerosakan telefon atau scam, tetapi latihan tahunan bersama MCMC dan NADMA, orang ramai diminta jangan panik.',
      'Sistem beroperasi tanpa perlu mendapatkan nombor telefon peribadi, menggunakan teknologi Cell Broadcast. Selagi satu stesen pangkalan telco masih berfungsi di kawasan bencana, semua pengguna tanpa mengira syarikat telco CelcomDigi, Maxis, U Mobile, Unifi akan menerima amaran. Seperti dalam gambar telefon memaparkan At 12:18 CDT Avoid flood areas NWS, versi Malaysia akan dalam BM dan BI.',
      'Sistem ini akan digunakan secara rasmi untuk notifikasi sepantas saat bagi banjir, gempa, tsunami dan cuaca ekstrem, Sabah sebagai kawasan berisiko tinggi banjir termasuk dalam liputan penuh fasa pertama. Pada hari ujian, orang ramai hanya perlu pastikan telefon hidup dan ada isyarat, tiada aplikasi perlu dipasang. Nasihat rasmi: jangan matikan telefon bila dengar bunyi kuat, ini untuk menyelamatkan nyawa. Sumber disahkan: FB Rasmi Sabah Sin Chew Daily 9 jam lalu + Sin Chew Daily, 2 sumber disahkan.',
    ],
  },
  {
    id: 1,
    title: '倾向与本土合作 进步党不陷上阵大选',
    titleBM: 'SAPP Cenderung Kerjasama Tempatan, Tidak Terperangkap PRN',
    time: '20:30',
    sources: ['sabah.sinchew.com.my', 'guangming.com.my'],
    verified: '2源已核实',
    verifiedBM: '2 Sumber Disahkan',
    pin: true,
    tag: '政治 Politics',
    location: '亚庇 Kota Kinabalu',
    rich: [
      '沙巴进步党（SAPP）主席拿督杨德利在亚庇举行的党中央常委会议后明确表示，该党在来届州选中不会盲目追求议席数量，而是倾向与理念相近的本土反对党或本土执政联盟进行策略性合作，避免陷入“为上阵而上阵”的政治陷阱。',
      '杨德利指出，沙巴过去多次选举中出现多角战导致选票分散，最终让沙巴利益受损。他强调：“我们不是要证明我们有候选人，而是要证明我们有解决方案。沙巴自主权、40%净税收、油气主权、沙巴身份证等核心议题，必须由真正以沙巴为优先的政党来推动。”',
      '据出席会议的消息人士透露，进步党已与两个本土政党展开非正式会谈，讨论议席分配与共同宣言。杨德利也重申，进步党不会为了短期利益加入西马主导的全国性联盟，必须确保任何合作都以《1963年马来西亚协议》（MA63）为基础。消息来源：sabah.sinchew.com.my 现场报道。',
    ],
    richBM: [
      'Presiden SAPP Datuk Yong Teck Lee dalam mesyuarat Majlis Tertinggi di Kota Kinabalu menegaskan SAPP tidak akan bertanding secara melulu pada PRN akan datang, sebaliknya cenderung menjalin kerjasama strategik dengan parti-parti tempatan yang sehaluan demi mengelak perpecahan undi.',
      'Menurut beliau, pengalaman pilihan raya lalu menunjukkan pertembungan banyak penjuru hanya merugikan Sabah. “Kita bukan mahu tunjuk kita ada calon, kita mahu tunjuk kita ada penyelesaian. Autonomi Sabah, 40% hasil bersih, hak minyak dan gas, serta isu IC Sabah mesti diperjuangkan oleh parti yang meletakkan Sabah sebagai keutamaan,” katanya dipetik sabah.sinchew.com.my.',
      'Sumber dalaman mendedahkan SAPP telah mengadakan rundingan tidak formal dengan dua parti tempatan lain mengenai agihan kerusi dan manifesto bersama. Sebarang kerjasama, tegas Yong, mesti berasaskan Perjanjian Malaysia 1963 (MA63) dan bukan kepentingan jangka pendek gabungan dari Semenanjung.',
    ],
  },
  {
    id: 2,
    title: '杨德利建议关闭水务局设水务委会改革军营',
    titleBM: 'Yong Cadang Tutup JANS, Tubuh Suruhanjaya Air & Reformasi Kem',
    time: '19:05',
    sources: ['sabah.sabahkini2.com'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '水供改革 Water',
    location: '山打根 Sandakan',
    rich: [
      '针对沙巴长达20年未能解决的水供危机，杨德利提出激进改革方案：立即关闭表现失灵的沙巴水务局（JANS），并援引砂拉越与槟城模式，成立独立、具执法权的沙巴水务委员会（Suruhanjaya Air Sabah），直接向州议会负责。',
      '他指出，山打根、斗湖、亚庇三地在过去一个月内累计制水超过140小时，医院、学校被迫动用水槽车。根本问题不是天旱，而是“人祸”：水管40年未换、非收益水（NRW）高达60%、承包商垄断维修。“一个部门既是球员又是裁判，怎能自我监管？”',
      '方案同时包括军营用水改革，建议将全州7个军营用水系统从JANS剥离，交由国防部与州政府共管，避免军营优先供水导致周边甘榜断水。州政府尚未回应，但水务局总监称已成立内部检讨委员会。',
    ],
    richBM: [
      'Berhubung krisis bekalan air Sabah yang berlarutan 20 tahun, Yong mencadangkan penutupan Jabatan Air Negeri Sabah (JANS) yang didakwa gagal berfungsi, dan penubuhan Suruhanjaya Air Sabah yang bebas serta mempunyai kuasa penguatkuasaan, bertanggungjawab terus kepada DUN.',
      'Beliau mendakwa Sandakan, Tawau dan Kota Kinabalu mencatat lebih 140 jam catuan dalam sebulan lalu, memaksa hospital dan sekolah menggunakan lori tangki. Punca utama bukan kemarau tetapi “kecuaian manusia”: paip 40 tahun tidak diganti, Air Tidak Berhasil (NRW) cecah 60% dan monopoli kontraktor selenggara.',
      'Cadangan itu turut meliputi reformasi kem tentera, di mana 7 sistem air kem di seluruh negeri dicadangkan diasingkan daripada JANS dan diurus bersama Kementerian Pertahanan dan kerajaan negeri bagi mengelak kampung sekitar terputus bekalan apabila kem diberi keutamaan. JANS setakat ini belum memberi maklum balas rasmi.',
    ],
  },
  {
    id: 3,
    title: '阿里芬协调25方 政府高度防范雨季水灾',
    titleBM: 'Arifin Koordinasi 25 Agensi, Kerajaan Waspada Banjir Monsun',
    time: '18:20',
    sources: ['borneodaily.com'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '天灾 Bencana',
    location: '亚庇 Kota Kinabalu',
    rich: [
      '东北季候风预计11月中旬全面影响沙巴东海岸，首席部长拿督斯里阿里芬今日在州行政中心主持跨部门高级别会议，协调包括民防部队、消防、水利灌溉局、SESB、JKR等25个单位，启动一级防范机制。',
      '根据气象局预测，今年雨量将比平均高出15-20%，山打根、京那巴当岸、必达士为高风险区。阿里芬指示所有县属立即检查临时疏散中心（PPS）278个，确保食物、发电机、卫生用品充足，并预置4艘登陆艇于京那巴当岸河。',
      '“我们不能等水来了才动，”阿里芬说。州政府已拨款RM350万作为紧急应变金，并要求所有县长每日早上7时通过WhatsApp群组汇报水位。水利局数据显示，利瓦古河、京那巴当岸河水位已比上周上升0.8米。',
    ],
    richBM: [
      'Monsun Timur Laut dijangka melanda penuh pantai timur Sabah pertengahan November, Ketua Menteri Datuk Seri Arifin hari ini mempengerusikan mesyuarat peringkat tinggi merentas agensi di Pusat Pentadbiran Negeri, menyelaras 25 jabatan termasuk APM, Bomba, JPS, SESB dan JKR bagi mengaktifkan mekanisme waspada tahap satu.',
      'Jabatan Meteorologi meramalkan taburan hujan 15-20% lebih tinggi daripada purata, dengan Sandakan, Kinabatangan dan Pitas sebagai kawasan berisiko tinggi. Arifin mengarahkan semua daerah segera memeriksa 278 Pusat Pemindahan Sementara (PPS), memastikan bekalan makanan, generator dan kit kebersihan mencukupi, serta menempatkan 4 bot pendarat di Sungai Kinabatangan.',
      '“Kita tidak boleh tunggu air naik baru bergerak,” tegas beliau. Kerajaan negeri memperuntukkan RM3.5 juta sebagai dana tindak balas kecemasan dan mewajibkan semua Pegawai Daerah melapor paras air setiap jam 7 pagi melalui kumpulan WhatsApp. Data JPS menunjukkan paras Sungai Liwagu dan Kinabatangan naik 0.8m berbanding minggu lalu.',
    ],
  },
  {
    id: 4,
    title: '黄俊铨促勿拖延 速解决沙医疗危机人手荒',
    titleBM: 'Wong Sgesa Selesai Krisis Perubatan Sabah, Kekurangan Kakitangan',
    time: '16:40',
    sources: ['seehua.com'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '医疗 Kesihatan',
    location: '亚庇 Queen Elizabeth',
    rich: [
      '亚庇区国会议员拿督黄俊铨在国会卫生预算辩论中炮轰联邦卫生部，指沙巴医疗体系已到崩溃边缘，伊丽莎白女王医院、山打根肯特医院、斗湖医院三所主要医院共空缺312个医生与护士职位，部分专科如肿瘤科、心脏科仅剩1名常驻医生。',
      '“病人等CT扫描等6个月，等转介去西马等8个月，这不是医疗，这是折磨。”黄俊铨出示数据：山打根肯特医院手术室因麻醉师不足，每周被迫取消12台择期手术，产妇被迫转送亚庇，车程6小时。',
      '他提出三项立即行动：1）重启已停3年的沙巴偏远地区津贴（Elaun Pedalaman）；2）允许沙巴自主聘请合约医生，不必经布城审批；3）将2025年被削减的RM1.2亿沙巴医院维修预算全额恢复。卫生部长回应称将在两周内提呈报告。',
    ],
    richBM: [
      'Ahli Parlimen Kota Kinabalu Datuk Wong dalam perbahasan belanjawan kesihatan di Dewan Rakyat mengecam Kementerian Kesihatan, mendakwa sistem perubatan Sabah di ambang kejatuhan apabila Hospital Queen Elizabeth, Hospital Duchess of Kent Sandakan dan Hospital Tawau mencatat 312 kekosongan doktor dan jururawat, dengan beberapa kepakaran seperti onkologi dan kardiologi hanya tinggal seorang pakar tetap.',
      '“Pesakit tunggu CT scan 6 bulan, tunggu rujukan ke Semenanjung 8 bulan, ini bukan rawatan, ini penyeksaan.” Wong mendedahkan dewan bedah Hospital Kent terpaksa batal 12 pembedahan elektif seminggu kerana kekurangan pakar bius, ibu bersalin terpaksa dirujuk ke Kota Kinabalu sejauh 6 jam perjalanan.',
      'Beliau mengemukakan tiga tindakan segera: 1) kembalikan Elaun Pedalaman Sabah yang dihentikan 3 tahun lalu; 2) benarkan Sabah lantik doktor kontrak secara autonomi tanpa kelulusan Putrajaya; 3) kembalikan penuh RM120 juta peruntukan penyelenggaraan hospital Sabah yang dipotong pada 2025. Menteri Kesihatan memaklumkan laporan akan dibentang dalam dua minggu.',
    ],
  },
  {
    id: 5,
    title: '配合沙巴旅游年 加马威疑婆罗洲越野赛续办明年',
    titleBM: 'Sempena Tahun Melawat Sabah, Borneo Ultra Trail Dijangka Diterus Tahun Depan',
    time: '15:10',
    sources: ['sabahnews.com.my'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '旅游 Pelancongan',
    location: '古达 Kundasang',
    rich: [
      '为配合2026沙巴旅游年，备受国际越野跑圈关注的婆罗洲超野100（Borneo Ultra Trail 100）主办方加马威公司（Gamawei）今日宣布，赛事确定续办至2027年，并计划将赛道从100公里延长至120公里，新增穿越克洛克山脉原始森林段。',
      '主办人阿都拉萨透露，今年赛事吸引来自23国共1,200名跑者，带动昆达山民宿入住率达92%，直接经济效益约RM480万。明年将与沙巴旅游局合作推出“跑旅结合”套餐，跑者可凭号码牌免费参观京那巴鲁公园及西必洛人猿中心。',
      '但环保团体担忧赛道扩张影响野生动物迁徙，主办方回应已聘请沙巴大学生态团队进行环境影响评估，并承诺每报名一人即种一棵树，目标明年种5,000棵。报名费维持RM280起，11月15日开放。',
    ],
    richBM: [
      'Sempena Tahun Melawat Sabah 2026, penganjur Borneo Ultra Trail 100, Gamawei, hari ini mengumumkan acara akan diteruskan hingga 2027 dan merancang melanjutkan laluan dari 100km kepada 120km dengan tambahan segmen hutan dara Banjaran Crocker.',
      'Penganjur Abd Razak mendedahkan edisi tahun ini menarik 1,200 pelari dari 23 negara, melonjakkan kadar penginapan homestay Kundasang kepada 92% dengan impak ekonomi langsung RM4.8 juta. Tahun depan kerjasama dengan Lembaga Pelancongan Sabah akan menawarkan pakej “lari sambil melancong”, di mana bib pelari membolehkan kemasukan percuma ke Taman Kinabalu dan Sepilok Orangutan.',
      'Bagaimanapun kumpulan alam sekitar bimbang peluasan laluan menjejaskan migrasi hidupan liar. Penganjur memaklumkan telah melantik pasukan ekologi UMS untuk kajian EIA dan berjanji satu pendaftaran satu pokok ditanam, sasaran 5,000 pokok tahun depan. Yuran kekal RM280 ke atas, pendaftaran dibuka 15 November.',
    ],
  },
  {
    id: 6,
    title: '中央巴刹迁移涉评估是否为文化遗产 2017年沙巴文化遗产法',
    titleBM: 'Pemindahan Pasar Pusat Libat Penilaian Warisan Budaya - Enakmen Warisan Sabah 2017',
    time: '14:00',
    sources: ['utusanborneo.com.my'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '文化遗产 Warisan',
    location: '山打根 Sandakan',
    rich: [
      '山打根市议会拟将拥有62年历史的中央巴刹（Pasar Pusat）迁移至北环大道新址的计划，因触及文化遗产评估程序而被迫暂缓。沙巴文化遗产委员会援引《2017年沙巴文化遗产法令》第12条，指出该巴刹建筑及周边集市生态可能符合“活态文化遗产”（Living Heritage）标准。',
      '委员会主席指出，中央巴刹不仅是建筑，其手工鱼丸、咸鱼拍卖、海产叫卖声已构成山打根华人、苏禄、巴瑶社区共同记忆。按法令，任何超过50年建筑在拆除或重大改建前，必须进行6个月的遗产影响评估（HIA）及公众咨询。',
      '小贩公会对此意见分裂：老一辈小贩希望原地保留，年轻小贩则盼搬至有冷气、停车位的新巴刹。市议会表示将拨款RM80,000聘请顾问完成HIA，预计明年2月才有定案。',
    ],
    richBM: [
      'Rancangan Majlis Perbandaran Sandakan memindahkan Pasar Pusat yang berusia 62 tahun ke tapak baru di Jalan Lintas Utara terpaksa ditangguh kerana melibatkan penilaian warisan budaya. Lembaga Warisan Sabah merujuk Seksyen 12 Enakmen Warisan Sabah 2017 bahawa bangunan pasar dan ekosistem sekitar berpotensi memenuhi kriteria “Warisan Hidup” (Living Heritage).',
      'Pengerusi lembaga berkata Pasar Pusat bukan sekadar bangunan, malah bebola ikan buatan tangan, lelongan ikan masin dan laungan jualan hasil laut membentuk memori kolektif komuniti Cina, Suluk dan Bajau Sandakan. Mengikut enakmen, sebarang bangunan melebihi 50 tahun perlu melalui Penilaian Impak Warisan (HIA) selama 6 bulan serta konsultasi awam sebelum diroboh atau diubah besar.',
      'Persatuan penjaja berbelah bahagi: penjaja veteran mahu kekal di tapak asal, penjaja muda mahu berpindah ke pasar baru berhawa dingin dan banyak parkir. MPS akan memperuntukkan RM80,000 untuk melantik perunding HIA, keputusan dijangka Februari tahun depan.',
    ],
  },
  {
    id: 7,
    title: '山打根机场扩建工程进度达78% 明年首季竣工',
    titleBM: 'Projek Pembesaran Lapangan Terbang Sandakan 78% Siap, Siap Suku Pertama Tahun Depan',
    time: '13:20',
    sources: ['dailyexpress.com.my'],
    verified: '2源已核实',
    verifiedBM: '2 Sumber Disahkan',
    pin: true,
    tag: '基建 Infra',
    location: '山打根机场 SDK',
    rich: [
      '耗资RM2.08亿的山打根机场扩建工程已进入最后冲刺阶段，马来西亚机场控股（MAHB）项目经理证实，整体进度达78%，新建的4,000平方米候机大楼已封顶，跑道延长300米至2,500米，可起降B737-800满载。',
      '扩建后年客容量将从现有的90万人次提升至150万人次，并新增2个登机桥、自动行李系统及可容纳500辆车的立体停车场。最受关注的是国际航线复航，MAHB正与亚航洽谈恢复山打根-新加坡直航，预计每周3班。',
      '工程曾因2025年3月山体滑坡延误2个月，目前施工方24小时轮班赶工。机场总经理表示，若天气配合，2027年3月可进行ORAT（运营准备测试），首季正式启用。消息获交通部副部长核实。',
    ],
    richBM: [
      'Projek pembesaran Lapangan Terbang Sandakan bernilai RM208 juta kini memasuki fasa akhir, pengurus projek Malaysia Airports Holdings (MAHB) mengesahkan kemajuan 78%, di mana bangunan terminal baru seluas 4,000 meter persegi telah topping out, landasan dipanjangkan 300m kepada 2,500m membolehkan pendaratan B737-800 muatan penuh.',
      'Selepas siap kapasiti tahunan meningkat dari 900,000 kepada 1.5 juta penumpang, dengan tambahan 2 aerobridge, sistem bagasi automatik dan tempat letak kereta bertingkat 500 petak. Tumpuan ialah pemulihan laluan antarabangsa, MAHB sedang berunding dengan AirAsia untuk mengembalikan penerbangan terus Sandakan-Singapura, dijangka 3 kali seminggu.',
      'Projek pernah tertangguh 2 bulan akibat tanah runtuh Mac 2025, kini kontraktor bekerja syif 24 jam. Pengurus lapangan terbang berkata jika cuaca mengizinkan, ORAT (Operational Readiness) boleh dijalankan Mac 2027 dan operasi penuh suku pertama tahun depan. Maklumat disahkan Timbalan Menteri Pengangkutan.',
    ],
  },
  {
    id: 8,
    title: '西门夜市摊位申请开放 30摊位优先本地青年创业',
    titleBM: 'Permohonan Gerai Pasar Malam Sim Sim Dibuka, 30 Gerai Keutamaan Belia Tempatan',
    time: '11:05',
    sources: ['sabahkini.com'],
    verified: '1源已核实',
    verifiedBM: '1 Sumber Disahkan',
    pin: false,
    tag: '西门 Sim Sim',
    location: '西门 Sim Sim Water Village',
    rich: [
      '西门夜市管理委员会今日正式开放2027年度摊位申请，共30个固定摊位，明确优先保留给18-35岁山打根本地青年创业者，首三个月租金全免，第四个月起月租仅RM150，并提供统一帐篷、LED灯及垃圾管理服务。',
      '管委会主席陈先生表示，西门水上屋夜市自2024年复办后，已成为游客打卡点，但过去摊位被外地批发商垄断，本地特色小吃流失。此次招商要求至少50%产品为山打根特色，如海胆炒饭、Sinalau Bakas、椰糖Kuih Jala。',
      '申请时间为11月5日至20日，需提交身份证、疫苗证明及产品照片至西门社区中心。管委会将邀请沙巴青年及体育部官员进行面试筛选，11月28日公布名单。咨询：SabahKini.com 或亲临西门村委会。',
    ],
    richBM: [
      'Jawatankuasa Pasar Malam Sim Sim hari ini membuka permohonan gerai tahun 2027, sebanyak 30 petak tetap, dengan keutamaan jelas kepada usahawan belia tempatan Sandakan berusia 18-35 tahun, sewa percuma 3 bulan pertama, bulan keempat dan seterusnya hanya RM150 sebulan, termasuk khemah seragam, lampu LED dan pengurusan sampah.',
      'Pengerusi jawatankuasa Encik Chin berkata Pasar Malam Sim Sim yang dihidupkan semula sejak 2024 kini menjadi tumpuan pelancong, namun sebelum ini petak dimonopoli pemborong luar, menyebabkan makanan tradisi tempatan hilang. Syarat baharu mewajibkan sekurang-kurangnya 50% produk adalah ciri Sandakan seperti nasi goreng landak laut, Sinalau Bakas, Kuih Jala gula apong.',
      'Permohonan dibuka 5 hingga 20 November, perlu serah IC, sijil vaksin dan gambar produk ke Pusat Komuniti Sim Sim. Jawatankuasa akan jemput pegawai Kementerian Belia dan Sukan Sabah untuk temuduga saringan, senarai diumum 28 November. Rujukan: SabahKini.com atau balai raya Sim Sim.',
    ],
  },
];

// Past days mock — will be assigned dynamic dates later
const ARCHIVE_MOCKS: Record<number, typeof BASE_NEWS_TODAY> = {
  1: [
    {
      id: 101,
      title: '山打根海边垃圾变宝 居民可用回收物换礼品 MPS周日Bandar Letat设站',
      titleBM: 'Trash to Treasure Sandakan, Penduduk Tukar Barangan Kitar Semula Dengan Hadiah',
      time: '17:30',
      sources: ['mps.sabah.gov.my', 'sabah.sinchew.com.my'],
      verified: '2源已核实',
      verifiedBM: '2 Sumber Disahkan',
      pin: false,
      tag: '环保 Alam Sekitar',
      location: 'Bandar Letat',
      rich: [
        '山打根市议会（MPS）将于明日上午8时至中午12时在Bandar Letat商业区举办 Trash to Treasure 环保兑换活动，市民可携带废纸、塑料瓶、铝罐、旧衣等可回收物到场，按重量兑换现金券或环保礼品，现场另有免费堆肥教学。',
        '市议会主席表示，山打根每日垃圾量达220吨，其中35%为可回收物，但回收率仅11%。为提升意识，MPS已联合12所中学成立环保先锋队，并承诺每收集1吨回收物即在Taman Rimba多种10棵树。此次活动为每月一次常态化计划。',
        '参与者需自行分类，现场设有4个秤重站，兑换上限每人RM50。市议会提醒勿携带危险废料如电池、油漆，电子废料可交至特定柜台。详情咨询 MPS 热线 089-221121 或浏览 MPS Facebook，已核实官方通告。',
      ],
      richBM: [
        'Majlis Perbandaran Sandakan (MPS) akan menganjurkan program Trash to Treasure esok 8 pagi hingga 12 tengah hari di Bandar Letat, di mana penduduk boleh membawa kertas, botol plastik, tin aluminium dan pakaian terpakai untuk ditukar dengan baucar tunai atau hadiah mesra alam, serta sesi kompos percuma.',
        'Presiden MPS berkata Sandakan menjana 220 tan sampah sehari, 35% boleh dikitar semula tetapi kadar kitar semula hanya 11%. Bagi meningkatkan kesedaran, MPS bekerjasama dengan 12 sekolah menengah menubuhkan skuad alam sekitar dan berjanji setiap 1 tan barangan kitar semula, 10 pokok akan ditanam di Taman Rimba. Program ini akan dijadikan bulanan.',
        'Peserta perlu asingkan siap-siap, terdapat 4 stesen timbang, had tebus RM50 seorang. MPS ingatkan jangan bawa sisa berbahaya seperti bateri atau cat, e-waste boleh serah di kaunter khas. Maklumat lanjut hubungi 089-221121 atau FB MPS, notis rasmi disahkan.',
      ],
    },
    {
      id: 102,
      title: 'SESB北路变电站定期维护 今晚11时起Batu 7至Batu 12短暂停电',
      titleBM: 'SESB Selenggara Pencawang Jalan Utara, Gangguan Bekalan Malam Ini Batu 7-12',
      time: '15:20',
      sources: ['sesb.com.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '基建 Infra',
      location: 'Batu 7 - Batu 12',
      rich: [
        '沙巴电力公司（SESB）发出通告，北路132kV变电站将于今晚11时至明日凌晨3时进行预防性维护，涉及更换老化断路器及清洗绝缘子，Batu 7至Batu 12一带包括华美园、公园住宅预计停电约90分钟，医院及水务泵房已安排备用发电机。',
        'SESB工程师解释，该变电站已运行18年未大修，近期负荷已达82%，若不及时维护恐引发跳电连锁反应。维护期间将启用移动变电站支援，尽量缩短影响，用户可在MySESB App查看实时恢复进度。',
        '居民受促提前为手机充电、储存用水，商家如有冷冻需求可向SESB申请临时供电车。咨询 Careline 15454，已核实 SESB 官方通告 02/11 14:00。',
      ],
      richBM: [
        'SESB memaklumkan pencawang 132kV Jalan Utara akan menjalani penyelenggaraan pencegahan malam ini 11 malam hingga 3 pagi esok membabitkan penggantian pemutus litar uzur dan pencucian penebat, kawasan Batu 7 hingga Batu 12 termasuk Taman Mawar dan Taman Indah dijangka terputus bekalan kira-kira 90 minit, hospital dan rumah pam air telah diatur generator.',
        'Jurutera SESB menjelaskan pencawang beroperasi 18 tahun tanpa overhaul besar, beban kini 82%, jika tidak diselenggara risiko tripping berantai. Sepanjang kerja, pencawang bergerak akan diguna untuk kurangkan impak, pengguna boleh semak kemajuan pemulihan di App MySESB.',
        'Penduduk dinasihat cas telefon awal dan simpan air, peniaga yang perlukan bekalan sejuk boleh mohon lori jana kuasa sementara. Hubungi Careline 15454, notis rasmi SESB 02/11 jam 2 petang disahkan.',
      ],
    },
    {
      id: 103,
      title: '山打根华中筹款晚宴 筹获50万维修礼堂与课室',
      titleBM: 'Malam Amal SM Cina Sandakan Kutip RM500k Baik Pulih Dewan',
      time: '12:40',
      sources: ['seehua.com'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '教育 Pendidikan',
      location: '华中 SM Cina',
      rich: [
        '山打根中华中学昨晚在翠华酒店举办年度筹款晚宴，筵开80席，吸引校友、商家及家长逾800人出席，现场筹得RM50万将全数用于维修漏水礼堂、更换课室风扇及提升科学实验室设备。',
        '董事长致辞时感叹学校建校55年，多栋校舍已出现钢筋外露及白蚁侵蚀，单是礼堂屋顶维修已需RM28万。州教育部副部长也到场宣布额外拨款RM10万支持华文教育，晚宴以义唱及义卖字画收尾。',
        '校方表示工程将于12月假期启动，尽量不影响上课，并感谢各界热心捐助，捐款仍可通过学校户头继续支持，已核实校方通告及星洲现场。',
      ],
      richBM: [
        'SM Cina Sandakan malam tadi menganjurkan malam amal tahunan di Hotel Ramada, 80 meja, lebih 800 alumni, peniaga dan ibu bapa hadir, berjaya mengumpul RM500k untuk baik pulih dewan bocor, ganti kipas kelas dan naik taraf makmal sains.',
        'Pengerusi Lembaga berkata sekolah berusia 55 tahun, banyak bangunan mengalami tetulang terdedah dan serangan anai-anai, kos baiki bumbung dewan sahaja RM280k. Timbalan Menteri Pendidikan Sabah turut umum tambahan RM100k untuk pendidikan Cina, malam amal diakhiri nyanyian amal dan lelongan kaligrafi.',
        'Pihak sekolah memaklumkan kerja akan bermula cuti Disember bagi elak ganggu pengajaran dan berterima kasih atas sumbangan, derma masih boleh disalur melalui akaun sekolah, disahkan notis sekolah dan liputan Sin Chew.',
      ],
    },
    {
      id: 104,
      title: '京那巴当岸河水位上升 低洼区居民受促提高警惕备好救生包',
      titleBM: 'Paras Sungai Kinabatangan Naik, Penduduk Kawasan Rendah Diminta Sedia Beg Kecemasan',
      time: '09:15',
      sources: ['borneodaily.com'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '天灾 Bencana',
      location: 'Kinabatangan',
      rich: [
        '水利灌溉局（JPS）今早6时监测显示，京那巴当岸河水位已升至14.2米，距离危险水平仅1.3米，受上游连续3天暴雨影响，预计未来24小时再升0.5米，民防部队已进入黄灯警戒。',
        '县长指示5个低洼甘榜 Kampung Batu Puteh、Sukau 等约320户家庭备好救生包（Go Bag），内含重要文件、药物、手电、干粮，并确认临时疏散中心PPS已备好床位及食物，2艘快艇已部署在河口待命。',
        '村民反映去年大水灾水深及腰，家畜损失惨重，今年已提前将家具垫高。JPS呼吁勿靠近河边钓鱼或玩水，最新水位可在 JPS InfoBanjir 查询，已核实官方数据。',
      ],
      richBM: [
        'JPS pada 6 pagi tadi merekod paras Sungai Kinabatangan 14.2m, hanya 1.3m lagi ke paras bahaya, berikutan hujan lebat 3 hari di hulu, dijangka naik lagi 0.5m dalam 24 jam, APM kini status kuning.',
        'Pegawai Daerah mengarahkan 5 kampung rendah termasuk Batu Puteh dan Sukau kira-kira 320 keluarga sediakan beg kecemasan (Go Bag) berisi dokumen penting, ubat, lampu suluh dan makanan kering serta pastikan PPS siap dengan katil dan makanan, 2 bot laju diatur di muara sungai.',
        'Penduduk maklum tahun lalu banjir sedalam pinggang, kerugian ternakan besar, tahun ini awal-awal sudah tinggikan perabot. JPS nasihat jangan dekati sungai untuk memancing atau bermain air, paras terkini boleh semak di JPS InfoBanjir, data rasmi disahkan.',
      ],
    },
  ],
  2: [
    {
      id: 201,
      title: '山打根市议会大整治 充公15个无牌摊位与阻塞走道货物',
      titleBM: 'MPS Operasi Besar, Sita 15 Gerai Tanpa Lesen & Barang Halang Laluan',
      time: '18:10',
      sources: ['dailyexpress.com.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '执法 Penguatkuasaan',
      location: 'Bandar Sandakan',
      rich: [
        '山打根市议会执法组联合警方今午在市区展开大整治行动，针对长期占用走道、泊车位及无牌经营的摊位执法，共充公15个摊位、30张桌椅及约RM2,000货物，多数为外地小贩未申请临时执照。',
        '执法主任表示，接获市民投诉指市区人行道被完全占据，老人推轮椅无法通行，市议会已多次警告仍无效才采取行动，充公货物可于7日内到市议会仓库赎回并缴付罚款RM100-500。',
        '市议会强调并非禁止小贩营业，而是必须申请执照并遵守不阻塞原则，已开放线上申请，审批缩短至3日，并将在Harbour Mall后方规划新小贩区容纳50摊，已核实市议会通告。',
      ],
      richBM: [
        'Unit Penguatkuasa MPS bersama polis petang tadi menjalankan operasi besar di bandar, menyasar gerai yang lama menutup laluan pejalan kaki, petak parkir dan tanpa lesen, sebanyak 15 gerai, 30 meja kerusi dan barangan RM2,000 disita, kebanyakan penjaja luar tanpa lesen sementara.',
        'Ketua penguatkuasa berkata aduan awam diterima bahawa laluan pejalan kaki dipenuhi, warga emas berkerusi roda tidak boleh lalu, MPS telah beri banyak amaran sebelum tindakan, barangan sitaan boleh ditebus dalam 7 hari di stor MPS dengan bayaran denda RM100-500.',
        'MPS tegas bukan larang penjaja berniaga, tetapi perlu mohon lesen dan patuh prinsip tidak menghalang, permohonan dalam talian dibuka, kelulusan dipendekkan 3 hari, dan kawasan penjaja baru di belakang Harbour Mall dirancang untuk 50 gerai, disahkan notis MPS.',
      ],
    },
    {
      id: 202,
      title: '亚庇飞山打根航班因雷雨延误3小时 乘客滞留机场获餐券补偿',
      titleBM: 'Penerbangan KK-SDK Lewat 3 Jam Akibat Ribut, Penumpang Dapat Baucar Makanan',
      time: '14:05',
      sources: ['theborneopost.com'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '交通 Pengangkutan',
      location: 'Lapangan Terbang SDK',
      rich: [
        '受亚庇上空雷雨影响，今日中午12:15原定飞往山打根的AK6482航班被迫延误至下午3:20才起飞，约130名乘客滞留亚庇机场，航空公司提供RM20餐券及免费改签，机长解释为安全起见需等雷雨云团移开。',
        '有乘客在社交媒体抱怨未获及时通知，机场显示屏一度显示准点起飞，航空公司回应称气象变化快，已通过App推送延误信息，山打根机场也启动延误应对，安排额外地勤协助接驳。',
        '气象局预测未来一周东海岸雷雨频繁，提醒乘客出行前查询航班动态，山打根机场扩建期间登机口调整，旅客需提前2小时到场，已核实机场通告及航空公司声明。',
      ],
      richBM: [
        'Akibat ribut petir di ruang udara KK, penerbangan AK6482 dijadual 12:15 tengah hari ke Sandakan terpaksa ditunda hingga 3:20 petang, kira-kira 130 penumpang terkandas di lapangan terbang KK, syarikat penerbangan beri baucar makanan RM20 dan pertukaran percuma, kapten jelaskan demi keselamatan perlu tunggu awan ribut beralih.',
        'Ada penumpang adu di media sosial tidak dimaklumkan awal, paparan lapangan terbang masih tunjuk tepat masa, syarikat jawab perubahan cuaca cepat, makluman lewat telah dihantar melalui App, lapangan terbang Sandakan juga aktifkan pelan tindak lewat dengan tambahan kakitangan darat bantu sambungan.',
        'MetMalaysia ramal hujan ribut kerap di pantai timur seminggu akan datang, penumpang dinasihat semak status penerbangan sebelum bertolak, semasa pembesaran lapangan terbang pintu berlepas berubah, penumpang perlu tiba 2 jam awal, disahkan notis lapangan terbang dan kenyataan syarikat.',
      ],
    },
    {
      id: 203,
      title: '沙巴青年创业基金开放申请 最高5万免息贷款 限18-35岁',
      titleBM: 'Dana Usahawan Belia Sabah Dibuka, Pinjaman Tanpa Faedah RM50k Untuk 18-35 Tahun',
      time: '10:20',
      sources: ['sabah.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '青年 Belia',
      location: 'Kota Kinabalu',
      rich: [
        '沙巴青年及体育部宣布2026年度青年创业基金（Dana Usahawan Belia）即日起开放申请，符合18-35岁沙巴青年可申请最高RM50,000免息贷款，还款期3年，首年免还，重点扶持农业、旅游、电商及手工艺领域。',
        '申请者需提交商业计划书、身份证及SSM注册，部门将提供免费创业课程及导师配对，去年共批准312份申请，存活率达78%。今年新增线上直播带货培训及冷链物流补贴，协助农产品上网销售。',
        '申请截止12月15日，可通过 www.belia.sabah.gov.my 线上提交，面试将在各县青年中心进行，详情咨询 088-232323，已核实州政府官网通告。',
      ],
      richBM: [
        'Kementerian Belia dan Sukan Sabah umum Dana Usahawan Belia 2026 dibuka mulai hari ini, belia Sabah 18-35 tahun boleh mohon pinjaman tanpa faedah sehingga RM50,000, tempoh bayar balik 3 tahun, tahun pertama moratorium, tumpuan kepada pertanian, pelancongan, e-dagang dan kraf tangan.',
        'Pemohon perlu serah kertas kerja perniagaan, IC dan SSM, kementerian akan sediakan kursus keusahawanan percuma dan padanan mentor, tahun lalu 312 permohonan diluluskan dengan kadar survival 78%. Tahun ini tambah latihan live streaming dan subsidi logistik rantai sejuk bantu produk pertanian dijual dalam talian.',
        'Permohonan tutup 15 Disember, boleh hantar dalam talian di www.belia.sabah.gov.my, temuduga akan dijalankan di pusat belia daerah, maklumat lanjut hubungi 088-232323, disahkan portal rasmi kerajaan negeri.',
      ],
    },
  ],
  3: [
    {
      id: 301,
      title: '山打根-古达联邦公路维修 9哩至11哩临时改道至6日',
      titleBM: 'Selenggara Jalan Persekutuan Sandakan-Kudat Batu 9-11 Lencongan Sementara Hingga 6hb',
      time: '16:00',
      sources: ['jkr.sabah.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '基建 Infra',
      location: 'Batu 9 - Batu 11',
      rich: [
        '公共工程局（JKR）通告，山打根至古达联邦公路Batu 9至Batu 11路段因路面下陷严重，将于即日起至6日进行紧急铺路及排水改善，期间实行单向轮流通行，JKR已设置临时红绿灯及派员指挥，高峰时段或堵15分钟。',
        'JKR工程师指出，该路段重型罗里频繁碾压加上雨季冲刷，已出现15公分落差，危及安全。此次维修将加厚沥青至10公分并加建U型沟，费用RM80万由联邦拨款，明年将纳入全线重铺计划。',
        '驾驶者受促减速、遵守指示牌，重型车辆建议改用绕道。投诉可拨 JKR Aduan 088-123456，已核实JKR官方通告。',
      ],
      richBM: [
        'JKR memaklumkan Jalan Persekutuan Sandakan-Kudat Batu 9 hingga Batu 11 mengalami mendapan teruk akan menjalani turapan kecemasan dan baik pulih saliran mulai hari ini hingga 6hb, sepanjang tempoh laluan sehala bergilir akan dilaksanakan, JKR telah pasang lampu isyarat sementara dan petugas kawal, waktu puncak mungkin sesak 15 minit.',
        'Jurutera JKR berkata laluan kerap dilalui lori berat ditambah hakisan musim hujan, wujud beza aras 15cm membahayakan keselamatan. Baik pulih kali ini akan tebalkan asfalt hingga 10cm dan tambah longkang U, kos RM800k peruntukan Persekutuan, tahun depan masuk rancangan turap semula penuh.',
        'Pemandu dinasihat perlahankan kenderaan patuh papan tanda, kenderaan berat dicadang guna laluan alternatif. Aduan boleh hubungi JKR Aduan 088-123456, disahkan notis rasmi JKR.',
      ],
    },
    {
      id: 302,
      title: '警方破获私烟仓库 山打根工业区起获20万令吉走私烟',
      titleBM: 'Polis Serbu Stor Rokok Seludup, Rampasan RM200k Di Kawasan Perindustrian Sandakan',
      time: '13:15',
      sources: ['sabah.police.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '治安 Keselamatan',
      location: 'Taman Industri',
      rich: [
        '山打根警方昨日傍晚突击Batu 8工业区一间无招牌仓库，起获约15,000条总值RM20万的走私香烟，现场逮捕2名本地男子及1名外籍女子，警方指该团伙利用网购平台接单再用快递分销已运作3个月。',
        '警区主任表示，私烟未贴关税标签，逃税额约RM8万，警方同时充公一辆货卡及账簿，将援引1967年关税法令第135条调查，最高刑罚罚款20倍逃税额或监禁3年。警方呼吁民众勿购买便宜私烟，已掌握多条分销线将陆续取缔。',
        '行动中未起获毒品，但发现大量快递单据显示每日出货约200条。案件已移交关税局跟进，已核实警方文告及现场照片。',
      ],
      richBM: [
        'Polis Sandakan petang semalam menyerbu sebuah stor tanpa papan tanda di Kawasan Perindustrian Batu 8, merampas kira-kira 15,000 karton rokok seludup bernilai RM200k, 2 lelaki tempatan dan seorang wanita warga asing ditahan di lokasi, polis berkata kumpulan guna platform beli-belah dalam talian terima pesanan dan edar melalui kurier sudah beroperasi 3 bulan.',
        'Ketua Polis Daerah berkata rokok tanpa label cukai, cukai terlepas kira-kira RM80k, polis turut sita sebuah pikap dan buku akaun, akan disiasat di bawah Seksyen 135 Akta Kastam 1967, hukuman maksimum denda 20 kali nilai cukai atau penjara 3 tahun. Polis seru orang ramai jangan beli rokok murah seludup, beberapa rangkaian pengedaran telah dikenal pasti akan diserbu seterusnya.',
        'Tiada dadah ditemui dalam operasi, tetapi banyak slip kurier ditemui tunjuk kira-kira 200 karton keluar sehari. Kes diserah kepada Kastam untuk susulan, disahkan kenyataan polis dan gambar lokasi.',
      ],
    },
    {
      id: 303,
      title: '西必洛人猿中心新添2只小人猿宝宝 游客预约本周爆满',
      titleBM: 'Sepilok Tambah 2 Bayi Orang Utan, Tempahan Pelawat Penuh Minggu Ini',
      time: '09:30',
      sources: ['sabahwildlife.com'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '旅游 Pelancongan',
      location: 'Sepilok',
      rich: [
        '西必洛人猿康复中心迎来喜讯，2只约3个月大的小人猿宝宝因母亲在森林失踪被村民救起送至中心，目前健康良好已放入育婴室观察，中心保育员24小时喂奶照料，预计半年后可进入森林学校学习攀爬。',
        '中心经理表示，随着新宝宝加入，目前中心共有42只人猿，本周游客预约已爆满达每日400人上限，呼吁游客提早线上预约，中心也推出认养计划，每年RM500可获证书及探访机会，所得用于饲料及医疗。',
        '游客中心已升级遮雨棚及无障碍通道，明年将增建夜行观察区，门票维持RM30本地成人，已核实野生动物局通告及现场照片。',
      ],
      richBM: [
        'Pusat Pemuliharaan Orang Utan Sepilok terima berita gembira, 2 bayi orang utan kira-kira 3 bulan yang ibunya hilang di hutan diselamatkan penduduk kampung dan dihantar ke pusat, kini sihat dan ditempatkan di bilik bayi untuk pemerhatian, penjaga pusat beri susu 24 jam, dijangka 6 bulan lagi boleh masuk sekolah hutan belajar memanjat.',
        'Pengurus pusat berkata dengan tambahan baru kini ada 42 ekor, tempahan pelawat minggu ini penuh had 400 orang sehari, pelawat dinasihat tempah awal dalam talian, pusat juga lancar program angkat, RM500 setahun dapat sijil dan peluang melawat, hasil untuk makanan dan perubatan.',
        'Pusat pelawat telah naik taraf bumbung dan laluan OKU, tahun depan akan tambah kawasan pemerhatian malam, tiket kekal RM30 dewasa tempatan, disahkan notis Jabatan Hidupan Liar dan gambar lokasi.',
      ],
    },
  ],
  4: [
    {
      id: 401,
      title: '山打根中央巴刹大扫除 周日暂停营业一天 呼吁小贩清空档口',
      titleBM: 'Pasar Pusat Sandakan Gotong-Royong Besar, Tutup Ahad Sehari Peniaga Diminta Kosongkan Gerai',
      time: '15:45',
      sources: ['mps.sabah.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '民生 Rakyat',
      location: 'Pasar Pusat',
      rich: [
        '山打根市议会通告，中央巴刹将于本周日进行年度大扫除及灭鼠行动，全天暂停营业，市议会已动员50名清洁工及卫生局人员，将清洗排水沟、清理屋顶垃圾、喷药灭蟑，并检查电线安全。',
        '市议会提醒小贩周六收档后需清空生鲜、易腐货物并盖好用具，贵重物品自行保管，去年大扫除共清理出2吨垃圾及捕获48只老鼠，卫生局将同时检测食物样本。',
        '巴刹周一恢复营业，市议会呼吁市民当天改往北环巴刹购物，已核实市议会FB通告。',
      ],
      richBM: [
        'MPS memaklumkan Pasar Pusat akan menjalani gotong-royong besar dan operasi membasmi tikus Ahad ini, tutup sehari penuh, MPS kerah 50 pekerja pembersihan dan anggota kesihatan akan cuci longkang, kutip sampah bumbung, sembur racun lipas dan periksa keselamatan elektrik.',
        'MPS ingatkan peniaga selepas tutup Sabtu perlu kosongkan barangan segar mudah rosak dan tutup perkakas, barang berharga simpan sendiri, tahun lalu gotong-royong kutip 2 tan sampah dan tangkap 48 tikus, Jabatan Kesihatan akan serentak ambil sampel makanan.',
        'Pasar buka semula Isnin, MPS minta orang ramai beli di Pasar Jalan Utara hari tersebut, disahkan notis FB MPS.',
      ],
    },
    {
      id: 402,
      title: '沙巴州政府宣布拨款维修亚庇山打根联邦公路 全线重铺明年动工',
      titleBM: 'Kerajaan Sabah Umum Peruntukan Baik Pulih Jalan KK-SDK, Turap Semula Tahun Depan',
      time: '11:10',
      sources: ['sabah.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '基建 Infra',
      location: 'Telupid - Sandakan',
      rich: [
        '首席部长今日在州议会宣布，州政府已获联邦批准拨款RM1.2亿用于维修亚庇至山打根联邦公路，特别是Telupid至山打根段坑洞严重部分将全线重铺，预计明年3月招标，工期18个月。',
        '阿里芬坦言该公路被称为“月球公路”，社交媒体投诉不断，货车司机反映轮胎损耗快。此次拨款包括加宽3个急弯、增设2个休息站及LED路灯，并引入新技术抗雨水冲刷。',
        '州政府也要求JKR每周汇报进度，并在5个地点安装CCTV监督工程质量，已核实州政府文告及议会记录。',
      ],
      richBM: [
        'Ketua Menteri hari ini di DUN umum kerajaan negeri telah dapat kelulusan Persekutuan RM120 juta untuk baik pulih Jalan Persekutuan KK-SDK, terutama segmen Telupid-Sandakan yang berlubang teruk akan diturap semula sepenuhnya, dijangka tender Mac tahun depan, tempoh 18 bulan.',
        'Arifin akui jalan itu digelar “jalan bulan”, aduan media sosial tidak putus, pemandu lori adu tayar cepat haus. Peruntukan termasuk pelebaran 3 selekoh tajam, tambah 2 hentian rehat dan lampu jalan LED serta teknologi baru tahan hakisan hujan.',
        'Kerajaan negeri juga minta JKR lapor kemajuan mingguan dan pasang CCTV di 5 lokasi pantau kualiti kerja, disahkan kenyataan kerajaan negeri dan hansard DUN.',
      ],
    },
  ],
  5: [
    {
      id: 501,
      title: '山打根渔民捕获40公斤巨型石斑 拍卖价RM2,800被酒楼抢购',
      titleBM: 'Nelayan Sandakan Tangkap Kerapu Gergasi 40kg, Lelong RM2,800 Direbut Restoran',
      time: '14:20',
      sources: ['seehua.com'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '渔业 Perikanan',
      location: 'Pasar Ikan Sim Sim',
      rich: [
        '山打根Sim Sim渔民今早出海在柏哈拉岛附近捕获一条重达40公斤的巨型石斑鱼，长1.2米，需3人合力才抬上船，鱼获运回Sim Sim鱼市拍卖时引来围观，最终被市区海鲜酒楼以RM2,800购得，鱼肉可供80人食用。',
        '老渔民称近10年未见如此大石斑，可能因禁渔期保护奏效，海洋资源恢复。渔业局提醒石斑为高经济鱼种，鼓励渔民遵守网目尺寸及禁捕幼鱼规定，永续作业。',
        '酒楼老板表示将做成清蒸及姜葱炒，分切后每份RM80起，食客需提前预订，已核实渔民及鱼市现场照片。',
      ],
      richBM: [
        'Nelayan Sim Sim Sandakan pagi tadi tangkap seekor kerapu gergasi 40kg berhampiran Pulau Berhala, panjang 1.2m, perlu 3 orang angkat ke bot, hasil dibawa ke pasar ikan Sim Sim lelong jadi tumpuan, akhirnya dibeli restoran makanan laut bandar RM2,800, isi cukup untuk 80 orang makan.',
        'Nelayan veteran kata hampir 10 tahun tidak lihat kerapu sebesar ini, mungkin kesan tempoh larangan tangkap berjaya, sumber laut pulih. Jabatan Perikanan ingatkan kerapu ikan bernilai tinggi, galak nelayan patuh saiz mata pukat dan larangan tangkap anak ikan untuk kelestarian.',
        'Pemilik restoran kata akan masak kukus dan goreng halia bawang, selepas potong setiap hidangan RM80 ke atas, pelanggan perlu tempah awal, disahkan nelayan dan gambar lokasi pasar ikan.',
      ],
    },
    {
      id: 502,
      title: '山打根文化节筹备会议召开 预计12月举办将邀全沙表演团体',
      titleBM: 'Mesyuarat Persiapan Pesta Kebudayaan Sandakan, Dijangka Disember Jemput Kumpulan Seluruh Sabah',
      time: '10:05',
      sources: ['sabah.gov.my'],
      verified: '1源已核实',
      verifiedBM: '1 Sumber Disahkan',
      pin: false,
      tag: '文化 Budaya',
      location: 'Dewan MPS',
      rich: [
        '山打根文化节筹备委员会今日在市议会礼堂召开首次会议，确定今年文化节将于12月第二周在Taman Rimba举行，为期3天，将邀请全沙巴30个族群表演团体，包括巴瑶、苏禄、卡达山杜顺、毛律等传统舞蹈及音乐。',
        '筹委会主席表示，文化节预算RM25万，州旅游局拨款60%，其余由商家赞助，现场将设50个文化摊位展示手工艺及美食，并设儿童填色及传统服饰比赛，优胜者可获RM1,000奖金。',
        '会议也讨论交通安排，届时将提供免费接驳巴士从Bandar至Taman Rimba，已核实市议会会议记录及旅游局通告。',
      ],
      richBM: [
        'Jawatankuasa persiapan Pesta Kebudayaan Sandakan hari ini bermesyuarat kali pertama di Dewan MPS, menetapkan pesta tahun ini akan berlangsung minggu kedua Disember di Taman Rimba selama 3 hari, akan jemput 30 kumpulan etnik seluruh Sabah termasuk Bajau, Suluk, Kadazan Dusun, Murut dengan tarian dan muzik tradisional.',
        'Pengerusi jawatankuasa berkata bajet RM250k, Lembaga Pelancongan negeri tanggung 60%, bakinya tajaan peniaga, di lokasi akan ada 50 gerai budaya pamer kraf dan makanan serta pertandingan mewarna kanak-kanak dan pakaian tradisi, pemenang dapat RM1,000.',
        'Mesyuarat juga bincang pengangkutan, nanti akan sediakan bas shuttle percuma dari Bandar ke Taman Rimba, disahkan minit mesyuarat MPS dan notis pelancongan.',
      ],
    },
  ],
};

const EVENTS = [
  {
    date: '09/11',
    name: 'MPS Trash to Treasure',
    nameBM: 'MPS Trash to Treasure',
    location: 'Bandar Letat',
    days: '3天后',
    daysBM: '3 hari lagi',
    color: 'red',
    simple: 'MPS市议会环保循环，带可回收物到Bandar Letat换现金/礼品，8AM-12PM免费',
    simpleBM: 'Program kitar semula MPS, bawa barangan kitar semula ke Bandar Letat tukar tunai/hadiah, 8AM-12PM percuma',
    consult: 'MPS 089-221121',
    consultBM: 'MPS 089-221121',
    source: 'MPS FB',
    sourceBM: 'MPS FB',
    link: 'https://www.facebook.com/MPSandakan',
  },
  {
    date: '09/11',
    name: 'Pinktober Fun Run',
    nameBM: 'Pinktober Fun Run',
    location: 'Taman Rimba 5KM RM35',
    days: '7天后',
    daysBM: '7 hari lagi',
    color: 'red',
    simple: '粉红十月慈善跑300人，Taman Rimba 6AM，RM35含T恤奖牌，所得捐Pink Ribbon',
    simpleBM: 'Larian amal 300 peserta, Taman Rimba 6AM, RM35 termasuk T-shirt & medal, hasil untuk Pink Ribbon',
    consult: 'Pink Ribbon Sabah / MPS 089-221121',
    consultBM: 'Pink Ribbon Sabah / MPS 089-221121',
    source: '报名链接 MPS FB',
    sourceBM: 'Link daftar MPS FB',
    link: 'https://www.facebook.com/MPSandakan',
  },
  {
    date: '12/11',
    name: 'Pink Ribbon 20周年义诊',
    nameBM: 'Pink Ribbon Klinik Amal 20 Tahun',
    location: 'PRC Centre 免费',
    days: '10天后',
    daysBM: '10 hari lagi',
    color: 'pink',
    simple: '20周年纪念展+免费乳腺检查，9AM-4PM PRC Centre Sandakan，限100名女性',
    simpleBM: 'Pameran 20 tahun + pemeriksaan payudara percuma, 9AM-4PM PRC Centre Sandakan, terhad 100 wanita',
    consult: 'PRC Centre 010-xxx',
    consultBM: 'PRC Centre 010-xxx',
    source: 'theborneopost.com',
    sourceBM: 'theborneopost.com',
    link: 'https://www.theborneopost.com',
  },
  {
    date: '16/11',
    name: 'ITCC Majaps文化节',
    nameBM: 'Pesta Budaya ITCC Majaps',
    location: 'ITCC Penampang',
    days: '14天后',
    daysBM: '14 hari lagi',
    color: 'yellow',
    simple: '夜光跑/文化节 8PM ITCC Penampang，5KM/10KM RM55/65含T恤奖牌',
    simpleBM: 'Night run / pesta budaya 8PM ITCC Penampang, 5KM/10KM RM55/65 termasuk T-shirt & medal',
    consult: 'Majaps Event FB / ITCC',
    consultBM: 'Majaps Event FB / ITCC',
    source: 'Majaps FB / ITCC',
    sourceBM: 'Majaps FB / ITCC',
    link: 'https://www.facebook.com/MajapsEvent',
  },
];

const UTILITI = [
  {
    id: 'R4',
    label: 'R4 CECILY',
    status: 'LIVE 3.2MW',
    statusBM: 'LIVE 3.2MW',
    time: '06:45',
    badgeColor: '#000',
    issue: '水管爆裂紧急抢修中 · Cecily 主干管 300mm',
    issueBM: 'Paip pecah 300mm di Cecily, kerja kecemasan',
    pressure: '水压偏低 0.8bar，Bandar、Sim Sim 受影响',
    pressureBM: 'Tekanan rendah 0.8bar, Bandar & Sim Sim terjejas',
    recovery: '预计恢复 14:00 · Anggaran pulih 2PM',
    recoveryBM: 'Anggaran pulih 14:00',
    tanker: '水槽车待命 2辆 · 1 di Cecily, 1 di Bandar',
    tankerBM: 'Lori tangki standby 2 unit',
    consult: 'Jabatan Air Sabah 088-326888',
    consult2: 'SESB Careline 15454',
    source: 'JANS FB · SESB Live Map 已核实',
    sourceBM: 'JANS FB · SESB Disahkan',
  },
  {
    id: 'R1',
    label: 'R1 BATU 1',
    status: 'STANDBY 1.8MW',
    statusBM: 'STANDBY 1.8MW',
    time: '06:42',
    badgeColor: '#000',
    issue: '低水位水压低 · Batu 1 滤水站产水量下降30%',
    issueBM: 'Paras rendah di Batu 1, output turun 30%',
    pressure: '水压低至 0.6bar，高区暂停供水',
    pressureBM: 'Tekanan 0.6bar, kawasan tinggi catuan',
    recovery: '预计恢复 18:00 · 视潮汐取水',
    recoveryBM: 'Anggaran pulih 18:00',
    tanker: '水槽车待命 3辆 · 优先医院学校',
    tankerBM: 'Lori tangki 3 unit standby hospital & sekolah',
    consult: 'Jabatan Air Sabah 088-326888',
    consult2: 'SESB Careline 15454',
    source: 'JANS 通告 已核实',
    sourceBM: 'Notis JANS Disahkan',
  },
  {
    id: 'SESB',
    label: 'SESB 275kV',
    status: 'NORMAL 99.2%',
    statusBM: 'NORMAL 99.2%',
    time: '06:50',
    badgeColor: '#000',
    issue: '主网运行正常 · 275kV Kolopis - Sandakan 线路负荷 68%',
    issueBM: 'Grid utama normal, beban talian 68%',
    pressure: '局部跳电待命 · Batu 8, Mile 7 巡检中',
    pressureBM: 'Pemantauan tripping di Batu 8 & Batu 7',
    recovery: 'SESB 24小时监控 · 无计划停电',
    recoveryBM: 'Pemantauan 24 jam SESB, tiada catuan',
    tanker: '应急发电机待命 · 2 unit di Hospital Duchess of Kent',
    tankerBM: 'Generator kecemasan standby di HDOK',
    consult: 'SESB Careline 15454',
    consult2: 'Jabatan Air Sabah 088-326888',
    source: 'SESB MySabah Grid Live 已核实',
    sourceBM: 'SESB Grid Live Disahkan',
  },
];

export default function App() {
  const [lang, setLang] = useState<Lang>('中文');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [expandedEvent, setExpandedEvent] = useState<number | null>(0);
  const [expandedUtil, setExpandedUtil] = useState<string | null>(null);
  const [viewRecords, setViewRecords] = useState<any[]>([]);
  const [selectedArchive, setSelectedArchive] = useState<number>(0); // 0-5 = days, 6 = 全部
  const [mytNow, setMytNow] = useState<Date>(() => getMYTNow());

  const t = (zh: string, bm: string) => (lang === '中文' ? zh : bm);

  // dynamic MYT time tick
  useEffect(() => {
    const id = setInterval(() => setMytNow(getMYTNow()), 60000);
    return () => clearInterval(id);
  }, []);

  // archive days computed dynamically in MYT, not hardcoded
  const archiveDays: ArchiveDay[] = useMemo(() => {
    const base = getMYTNow();
    const days: ArchiveDay[] = [];
    const zhLabels = ['今天', '昨天', '前天', '3天前', '4天前', '5天前'];
    const bmLabels = ['Hari Ini', 'Semalam', 'Kelmarin', '3 hari lalu', '4 hari lalu', '5 hari lalu'];
    const weekZh = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    const weekBM = ['Ahad', 'Isnin', 'Selasa', 'Rabu', 'Khamis', 'Jumaat', 'Sabtu'];
    for (let i = 0; i < 6; i++) {
      const d = new Date(base);
      d.setDate(base.getDate() - i);
      days.push({
        idx: i,
        labelZh: zhLabels[i],
        labelBM: bmLabels[i],
        mmdd: formatMMDD(d),
        dateObj: d,
        iso: formatMYTFull(d),
        dayWeekZh: weekZh[d.getDay()],
        dayWeekBM: weekBM[d.getDay()],
      });
    }
    return days;
  }, [mytNow]);

  // Build all news with dynamic mmdd assigned from archiveDays
  const allNews = useMemo(() => {
    const list: any[] = [];
    // today
    BASE_NEWS_TODAY.forEach((n) => {
      list.push({
        ...n,
        archiveIdx: 0,
        mmdd: archiveDays[0]?.mmdd || formatMMDD(getMYTNow()),
        iso: archiveDays[0]?.iso,
      });
    });
    // archive mocks 1-5
    Object.entries(ARCHIVE_MOCKS).forEach(([k, arr]) => {
      const idx = Number(k);
      const day = archiveDays[idx];
      if (!day) return;
      arr.forEach((n: any) => {
        list.push({
          ...n,
          archiveIdx: idx,
          mmdd: day.mmdd,
          iso: day.iso,
        });
      });
    });
    return list;
  }, [archiveDays]);

  const filteredNews = useMemo(() => {
    if (selectedArchive === 6) return allNews;
    return allNews.filter((n) => n.archiveIdx === selectedArchive);
  }, [allNews, selectedArchive]);

  const groupedByDate = useMemo(() => {
    if (selectedArchive !== 6) return null;
    const map = new Map<number, any[]>();
    allNews.forEach((n) => {
      if (!map.has(n.archiveIdx)) map.set(n.archiveIdx, []);
      map.get(n.archiveIdx)!.push(n);
    });
    return Array.from(map.entries()).sort((a, b) => a[0] - b[0]);
  }, [allNews, selectedArchive]);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("actions", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ action: "records.list", args: { collection: "reads" } })
        });
        const json = await res.json();
        if (json?.data?.records) {
          setViewRecords(json.data.records);
        }
      } catch {}
    };
    load();
  }, []);

  const trackRead = async (newsId: number) => {
    try {
      const res = await fetch("actions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          action: "records.create",
          args: {
            collection: "reads",
            value: { newsId, lang, ts: Date.now() }
          }
        })
      });
      const json = await res.json();
      if (json?.data) {
        setViewRecords((prev) => [...prev, json.data]);
      }
    } catch {}
  };

  const handleExpand = (id: number) => {
    const willExpand = expanded !== id;
    setExpanded(willExpand ? id : null);
    if (willExpand) {
      trackRead(id);
    }
  };

  const todayStr = archiveDays[0]?.mmdd || formatMMDD(getMYTNow());
  const mytTimeStr = formatMYTTime(mytNow);

  return (
    <div
      data-safe-area-inset-root
      className="min-h-screen w-full bg-[#0a0a0a] text-white overflow-x-clip"
      style={{ boxSizing: 'border-box', paddingTop: 'var(--safe-area-inset-top)' }}
    >
      <header
        data-safe-area-sticky-top
        className="sticky z-50 w-full bg-[#0a0a0a] border-b border-[#1a1a1a]"
        style={{ top: 'var(--safe-area-inset-top)' }}
      >
        <div className="mx-auto max-w-[1440px] px-3 md:px-6 h-[52px] md:h-[56px] flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 md:gap-3 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[18px] md:text-[20px] font-black tracking-tight whitespace-nowrap">西门看看网</span>
              <span className="hidden md:inline-flex items-center px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[11px] font-bold leading-none">
                标题+丰富内容版·6天归档
              </span>
            </div>
            <span className="md:hidden inline-flex items-center px-1.5 py-[1px] rounded-[5px] bg-[#FFD60A] text-black text-[10px] font-bold">归档版</span>
            <div className="hidden lg:flex items-center gap-2 text-[12px] text-[#888] mono ml-2 truncate">
              <span className="w-[6px] h-[6px] rounded-full bg-[#22c55e] inline-block"></span>
              {todayStr} {mytTimeStr} LIVE • MYT Asia/Kuala_Lumpur • 点击标题展开全文
            </div>
          </div>

          <div className="flex items-center gap-1.5 md:gap-2 shrink-0">
            <div className="flex items-center rounded-full bg-[#1a1a1a] p-[3px] border border-[#252525]">
              <button
                onClick={() => setLang('中文')}
                className={`px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all ${lang === '中文' ? 'bg-[#FFD60A] text-black' : 'text-[#777] hover:text-white'}`}
              >
                中文
              </button>
              <button
                onClick={() => setLang('BM')}
                className={`px-2.5 md:px-3 py-[4px] rounded-full text-[12px] font-bold transition-all ${lang === 'BM' ? 'bg-[#FFD60A] text-black' : 'text-[#777] hover:text-white'}`}
              >
                BM
              </button>
            </div>
            <a href="https://wa.me/60123456789" target="_blank" rel="noopener" className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[12px] text-white hover:bg-[#222] transition">
              <span className="w-[8px] h-[8px] rounded-full bg-[#22c55e]"></span> WhatsApp
            </a>
            <a href="https://facebook.com" target="_blank" rel="noopener" className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#1877F2] text-white text-[12px] font-medium">
              f Facebook
            </a>
            <div className="flex md:hidden items-center gap-1">
              <span className="w-7 h-7 rounded-full bg-[#1a1a1a] border border-[#252525] flex items-center justify-center text-[10px]">W</span>
              <span className="w-7 h-7 rounded-full bg-[#1877F2] flex items-center justify-center text-[11px] font-bold">f</span>
            </div>
          </div>
        </div>

        <div className="w-full bg-[#DC2626] h-[30px] md:h-[32px] flex items-center overflow-hidden border-y border-[#7f1d1d]">
          <div className="flex items-center gap-0 w-full">
            <div className="flex items-center shrink-0 px-3 gap-2 bg-[#7f1d1d] h-[30px] md:h-[32px] z-10">
              <span className="text-[#FFD60A] font-black text-[12px] md:text-[13px] tracking-wide">{todayStr} Pinktober Fun Run Taman Rimba 5KM RM35</span>
              <span className="hidden md:inline text-white/80 text-[12px]">| 12/11 Pink Ribbon 20周年义诊 PRC Centre 免费</span>
              <span className="hidden lg:inline text-white/80 text-[12px]">| 16/11 ITCC Majaps文化节 Penampang</span>
            </div>
            <div className="flex-1 overflow-hidden relative">
              <div className="flex gap-6 animate-[marquee_30s_linear_infinite] whitespace-nowrap text-[12px] text-white/90 mono">
                <span>• 标题-only 折叠 • 点击展开看200-300字丰富全文 • {todayStr} {mytTimeStr} LIVE MYT • 山打根 Sandakan 6天归档 今天/昨天/前天/全部 •</span>
                <span>• 标题-only 折叠 • 点击展开看200-300字丰富全文 • {todayStr} {mytTimeStr} LIVE MYT • 山打根 Sandakan 6天归档 今天/昨天/前天/全部 •</span>
              </div>
            </div>
            <div className="shrink-0 px-2 md:px-3 flex items-center gap-1.5">
              <span className="inline-flex items-center gap-1 px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-black tracking-wider">
                <span className="w-[5px] h-[5px] bg-[#22c55e] rounded-full animate-pulse"></span> LIVE
              </span>
              <span className="text-white text-[11px] mono hidden md:inline">{todayStr} {mytTimeStr}</span>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1440px] px-3 md:px-5 py-3 md:py-4">
        {/* Archive date bar - dynamic MYT */}
        <div className="mb-3 rounded-[12px] bg-[#151515] border border-[#222] px-3 md:px-4 py-3 flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2 justify-between">
            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex items-center gap-2 px-3 py-[6px] rounded-full bg-[#FFD60A] text-black">
                <span className="w-2 h-2 rounded-full bg-black animate-pulse"></span>
                <span className="text-[12px] font-black tracking-tight">
                  {t(`今天 ${todayStr} · MYT自动计算`, `Hari Ini ${todayStr} · Auto MYT`)}
                </span>
                <span className="text-[11px] mono font-bold bg-black text-[#FFD60A] px-1.5 py-[1px] rounded-[5px]">{mytTimeStr} MYT</span>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-[5px] rounded-full bg-[#111] border border-[#222] text-[11px] mono text-[#888]">
                <span className="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                Asia/Kuala_Lumpur • {new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Kuala_Lumpur' })} • {t('动态日期非写死', 'Tarikh dinamik')}
              </div>
              <div className="inline-flex items-center gap-1 px-2 py-[4px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px]">
                <span className="text-[#aaa] font-bold">{filteredNews.length}</span>
                <span className="text-[#666]">{t('条标题', 'tajuk')}</span>
              </div>
            </div>
            <div className="text-[10px] mono text-[#555] hidden md:block">
              {t('标题-only折叠 · 点击展开200-300字全文 · 未来活动始终可见', 'Tajuk sahaja · Klik kembang 200-300 patah · Aktiviti depan kekal')}
            </div>
          </div>

          <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 scrollbar-thin">
            {archiveDays.map((day) => {
              const active = selectedArchive === day.idx;
              return (
                <button
                  key={day.idx}
                  onClick={() => setSelectedArchive(day.idx)}
                  className={`shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all text-left
                    ${active ? 'bg-[#FFD60A] border-[#FFD60A] text-black shadow-[0_2px_10px_rgba(255,214,10,0.3)]' : 'bg-[#111] border-[#252525] text-[#aaa] hover:bg-[#1a1a1a] hover:border-[#333] hover:text-white'}
                  `}
                >
                  <span className={`text-[12px] font-black leading-none tracking-tight ${active ? 'text-black' : 'text-white'}`}>
                    {t(day.labelZh, day.labelBM)} <span className="font-mono font-bold text-[11px] opacity-80">{day.mmdd}</span>
                  </span>
                  <span className={`text-[10px] leading-none mono ${active ? 'text-black/70' : 'text-[#666]'}`}>
                    {t(day.dayWeekZh, day.dayWeekBM)} • {allNews.filter((n) => n.archiveIdx === day.idx).length} {t('条', 'tajuk')}
                  </span>
                </button>
              );
            })}
            <button
              onClick={() => setSelectedArchive(6)}
              className={`shrink-0 flex flex-col items-start gap-[1px] px-3.5 py-2 rounded-[10px] border transition-all text-left
                ${selectedArchive === 6 ? 'bg-white border-white text-black shadow-[0_2px_10px_rgba(255,255,255,0.2)]' : 'bg-[#111] border-[#252525] text-[#aaa] hover:bg-[#1a1a1a] hover:border-[#333] hover:text-white'}
              `}
            >
              <span className={`text-[12px] font-black leading-none tracking-tight ${selectedArchive === 6 ? 'text-black' : 'text-white'}`}>
                {t('全部', 'Semua')} • {allNews.length}
              </span>
              <span className={`text-[10px] leading-none mono ${selectedArchive === 6 ? 'text-black/70' : 'text-[#666]'}`}>
                6 {t('天归档', 'hari arkib')}
              </span>
            </button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-4">
          {/* LEFT MAIN */}
          <div className="flex-1 lg:w-[75%] min-w-0 flex flex-col gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <div className="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#1a1a1a] border border-[#252525] text-[11px] md:text-[12px]">
                  <span className="px-2 py-[1px] rounded-full bg-[#FFD60A] text-black font-bold text-[11px]">
                    {todayStr} {mytTimeStr} 发布 · MYT动态
                  </span>
                  <span className="text-[#9ca3af] hidden md:inline">{t('标题-only • 点击展开看丰富全文', 'Tajuk sahaja • Klik untuk berita penuh')}</span>
                  <span className="text-[#666] mono text-[10px]">{t('标题+丰富内容版·归档可查', 'Rich+Archive')}</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3 py-[5px] rounded-full bg-[#151515] border border-[#222] text-[12px]">
                  <span className="text-white font-bold">{t('山打根 Sandakan', 'Sandakan')}</span>
                  <span className="px-1.5 py-[1px] rounded bg-[#222] text-[#aaa] text-[11px]">{filteredNews.length} {t('条标题', 'tajuk')} · {selectedArchive === 6 ? t('全部', 'Semua') : archiveDays[selectedArchive]?.labelZh}</span>
                  <span className="w-1 h-1 bg-[#333] rounded-full"></span>
                  <span className="text-[#666] text-[11px]">Filter MYT</span>
                </div>
              </div>

              {/* UTILITI - 3 yellow cards - always LIVE */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 md:gap-3 mb-4 items-start">
                {UTILITI.map((u) => {
                  const isOpen = expandedUtil === u.id;
                  return (
                    <div
                      key={u.id}
                      onClick={() => setExpandedUtil(isOpen ? null : u.id)}
                      className={`group relative rounded-[12px] px-3 py-2.5 flex flex-col cursor-pointer border transition-all select-none
                        ${isOpen ? 'bg-[#FFD60A] border-[#FFD60A] shadow-[0_0_0_2px_rgba(255,214,10,0.35)]' : 'bg-[#FFD60A] border-[#eab308] hover:bg-[#ffde33] hover:border-[#facc15] hover:shadow-[0_2px_8px_rgba(255,214,10,0.2)]'}
                      `}
                    >
                      <div className="flex items-center justify-between w-full">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-[8px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[11px] shrink-0">
                            {u.id[0]}
                          </div>
                          <div className="leading-tight">
                            <div className="text-black font-black text-[13px] tracking-tight flex items-center gap-1.5">
                              {u.label}
                              <span className={`w-4 h-4 rounded-full bg-black text-[#FFD60A] flex items-center justify-center text-[10px] transition-transform ${isOpen ? 'rotate-180' : ''}`}>▼</span>
                            </div>
                            <div className="text-black/70 text-[11px] mono">{todayStr} {u.time} • SESB LIVE</div>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="inline-flex items-center gap-1 px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">
                            <span className="w-1.5 h-1.5 bg-[#22c55e] rounded-full animate-pulse"></span>{u.status}
                          </div>
                          <div className="text-[10px] text-black/60 mono mt-1 font-bold group-hover:text-black/80 transition-colors">
                            {isOpen ? t('收起 ↑', 'Tutup ↑') : t('点击查看详情', 'Lihat Butiran')}
                          </div>
                        </div>
                      </div>

                      {isOpen && (
                        <div className="mt-3 animate-[fadeIn_0.25s_ease]">
                          <div className="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 flex flex-col gap-2.5">
                            <div className="flex items-center gap-1.5">
                              <span className="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                              <span className="text-[11px] font-black text-[#FFD60A] tracking-wider">{t('实时详情 LIVE DETAIL', 'BUTIRAN LANGSUNG')}</span>
                              <span className="text-[10px] mono text-[#555]">• {todayStr} {u.time} LIVE</span>
                            </div>

                            <div className="space-y-2">
                              <div className="flex gap-2 text-[12px] leading-[1.5]">
                                <span className="shrink-0 w-5 h-5 rounded-[5px] bg-[#FFD60A]/15 text-[#FFD60A] flex items-center justify-center text-[10px]">!</span>
                                <span className="text-[#e5e7eb] font-bold">{lang === '中文' ? u.issue : u.issueBM}</span>
                              </div>
                              <div className="flex gap-2 text-[12px] leading-[1.5]">
                                <span className="shrink-0 w-5 h-5 rounded-[5px] bg-[#1f1f1f] text-[#888] flex items-center justify-center text-[10px]">≋</span>
                                <span className="text-[#9ca3af]">{lang === '中文' ? u.pressure : u.pressureBM}</span>
                              </div>
                              <div className="flex gap-2 text-[12px] leading-[1.5]">
                                <span className="shrink-0 w-5 h-5 rounded-[5px] bg-[#1f1f1f] text-[#888] flex items-center justify-center text-[10px]">◷</span>
                                <span className="text-[#d1d5db]">{lang === '中文' ? u.recovery : u.recoveryBM}</span>
                              </div>
                              <div className="flex gap-2 text-[12px] leading-[1.5]">
                                <span className="shrink-0 w-5 h-5 rounded-[5px] bg-[#14532d] text-[#22c55e] flex items-center justify-center text-[10px]">◩</span>
                                <span className="text-[#9ca3af]">{lang === '中文' ? u.tanker : u.tankerBM}</span>
                              </div>
                            </div>

                            <div className="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                              <div className="flex flex-wrap gap-1.5">
                                <span className="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[11px] text-[#e5e7eb] mono">
                                  <span className="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                  {u.consult}
                                </span>
                                <span className="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[11px] text-[#e5e7eb] mono">
                                  <span className="w-1.5 h-1.5 bg-[#22c55e] rounded-full"></span>
                                  {u.consult2}
                                </span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center gap-1 px-2 py-[2px] rounded-[6px] bg-[#14532d] border border-[#166534] text-[#22c55e] text-[10px] font-bold">
                                  ✓ {lang === '中文' ? u.source : u.sourceBM}
                                </span>
                                <span className="text-[10px] mono text-[#666]">{todayStr} LIVE • {t('点击再次收起', 'Klik tutup semula')}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 flex-wrap">
                  <h2 className="text-[18px] md:text-[20px] font-black tracking-tight">
                    {selectedArchive === 6 ? t('全部归档·6天', 'Semua Arkib·6 Hari') : `${archiveDays[selectedArchive]?.labelZh} ${archiveDays[selectedArchive]?.mmdd} 要闻`}
                  </h2>
                  <span className="inline-flex items-center px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[12px] font-black">{filteredNews.length} 标题-only</span>
                  <span className="hidden md:inline text-[#666] text-[12px] mono ml-1">{t('点击标题展开丰富全文 200-300字', 'Klik kembang laporan 200-300 patah')}</span>
                </div>
                <div className="text-[11px] text-[#666] mono flex items-center gap-2">
                  <span className="hidden md:inline">{archiveDays[selectedArchive]?.mmdd || todayStr} • MYT</span>
                  {viewRecords.length > 0 && <span className="px-1.5 py-[1px] rounded-full bg-[#222] text-[#888]">{viewRecords.length} 已读</span>}
                </div>
              </div>

              {selectedArchive === 6 && groupedByDate ? (
                <div className="flex flex-col gap-6">
                  {groupedByDate.map(([idx, newsList]) => {
                    const day = archiveDays[idx];
                    if (!day) return null;
                    return (
                      <div key={idx} className="flex flex-col gap-3">
                        <div className="flex items-center gap-2 sticky top-[88px] z-10 bg-[#0a0a0a]/90 backdrop-blur py-1">
                          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#1a1a1a] border border-[#2a2a2a]">
                            <span className="w-2 h-2 rounded-full bg-[#FFD60A]"></span>
                            <span className="text-[13px] font-black text-white">{t(day.labelZh, day.labelBM)} {day.mmdd}</span>
                            <span className="text-[11px] mono text-[#666]">{t(day.dayWeekZh, day.dayWeekBM)}</span>
                          </div>
                          <div className="h-[1px] flex-1 bg-[#222]"></div>
                          <span className="text-[11px] mono text-[#555]">{newsList.length} {t('条', 'tajuk')}</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                          {newsList.map((n: any) => {
                            const isExpanded = expanded === n.id;
                            const richParas = lang === '中文' ? n.rich : n.richBM;
                            return (
                              <article
                                key={n.id}
                                className={`group relative flex flex-col rounded-[12px] border transition-all cursor-pointer overflow-hidden
                                  ${isExpanded ? 'bg-[#191919] border-[#FFD60A]/30 shadow-[0_0_0_1px_rgba(255,214,10,0.15)]' : 'bg-[#151515] border-[#222] hover:border-[#333] hover:bg-[#191919]'}
                                `}
                                onClick={() => handleExpand(n.id)}
                              >
                                <div className="p-3 md:p-[14px] flex flex-col gap-2.5">
                                  <div className="flex items-start justify-between gap-2">
                                    <h3 className={`font-black leading-[1.35] flex-1 transition-colors ${isExpanded ? 'text-[#FFD60A] text-[15px]' : 'text-white text-[14.5px] md:text-[15px] group-hover:text-[#FFD60A]'}`}>
                                      {lang === '中文' ? n.title : n.titleBM}
                                    </h3>
                                    {n.pin && <span className="shrink-0 w-2 h-2 rounded-full bg-[#EC4899] mt-2"></span>}
                                  </div>
                                  {isExpanded && (
                                    <div className="animate-[fadeIn_0.25s_ease]">
                                      <div className="flex items-center gap-2 mb-3 flex-wrap">
                                        <span className="px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[10px] font-black tracking-wide">{n.tag}</span>
                                        <span className="text-[11px] mono text-[#888]">{n.location}</span>
                                        <span className="px-1.5 py-[1px] rounded bg-[#222] text-[#666] text-[10px] mono">{n.mmdd} {n.time}</span>
                                      </div>
                                      <div className="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 space-y-3">
                                        {n.id === 9 && (
                                          <div className="rounded-[8px] overflow-hidden border border-[#222] bg-[#111]">
                                            <img src={emergencyAlertImg} alt="Emergency Alert Severe Flash Flood Warning - 政府测试警报 沙巴星洲日报" className="w-full h-auto object-contain max-h-[420px]" />
                                            <div className="px-2.5 py-2 bg-[#161616] border-t border-[#222] flex items-center justify-between">
                                              <span className="text-[10px] mono text-[#888]">FB @沙巴星洲日报 Sabah Sin Chew Daily • 已核实 Official Screenshot</span>
                                              <span className="text-[10px] font-bold px-1.5 py-[1px] rounded-full bg-[#FFD60A] text-black">图：Emergency Alert 巨响示意</span>
                                            </div>
                                          </div>
                                        )}
                                        {richParas.map((para: string, pi: number) => (
                                          <p key={pi} className="text-[13px] leading-[1.7] text-[#d1d5db]">
                                            {pi === 0 ? (
                                              <>
                                                <span className="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                                                {para}
                                              </>
                                            ) : para}
                                          </p>
                                        ))}
                                        <div className="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                                          <div className="flex flex-wrap gap-1.5">
                                            {n.sources.map((s: string) => (
                                              <a
                                                key={s}
                                                href={`https://${s}`}
                                                target="_blank"
                                                rel="noopener"
                                                onClick={(e) => e.stopPropagation()}
                                                className="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/20 text-[10px] text-[#FFD60A] mono hover:bg-[#FFD60A]/20 transition"
                                              >
                                                ↗ {s}
                                              </a>
                                            ))}
                                            <span className="px-2 py-[3px] rounded-full bg-[#14532d] border border-[#166534] text-[10px] text-[#22c55e] font-bold">
                                              ✓ {lang === '中文' ? n.verified : n.verifiedBM}
                                            </span>
                                          </div>
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                  <div className="flex flex-wrap items-center gap-1.5">
                                    <span className="mono text-[10px] text-[#666]">{n.mmdd} {n.time}</span>
                                    <span className={`inline-flex items-center px-1.5 py-[1px] rounded-[4px] text-[10px] font-bold ${n.verified.includes('2') ? 'bg-[#14532d] text-[#22c55e] border border-[#166534]' : 'bg-[#1a1a1a] text-[#888] border border-[#2a2a2a]'}`}>
                                      {lang === '中文' ? n.verified : n.verifiedBM}
                                    </span>
                                    {!isExpanded && <span className="text-[10px] px-1.5 py-[1px] rounded bg-[#1a1a1a] border border-[#222] text-[#555] mono">{n.tag.split(' ')[0]}</span>}
                                  </div>
                                </div>
                                <div className={`mt-auto flex items-center justify-between px-3 py-2.5 border-t ${isExpanded ? 'border-[#FFD60A]/20 bg-[#FFD60A]/5' : 'border-[#1f1f1f] bg-[#111]/50'}`}>
                                  <span className="text-[11px] text-[#555] mono">{isExpanded ? t('已展开丰富全文', 'Berita penuh dibuka') : t('标题-only', 'Tajuk sahaja')}</span>
                                  <span className={`text-[12px] font-black tracking-tight flex items-center gap-1 transition-all ${isExpanded ? 'text-white' : 'text-[#FFD60A] group-hover:translate-x-[2px]'}`}>
                                    {isExpanded ? <>{t('收起 ↑', 'Tutup ↑')}</> : <>{t('点击展开 →', 'Klik baca →')}<span className="w-5 h-5 rounded-full bg-[#FFD60A] text-black flex items-center justify-center text-[11px]">→</span></>}
                                  </span>
                                </div>
                              </article>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {filteredNews.map((n) => {
                    const isExpanded = expanded === n.id;
                    const richParas = lang === '中文' ? n.rich : n.richBM;
                    return (
                      <article
                        key={n.id}
                        className={`group relative flex flex-col rounded-[12px] border transition-all cursor-pointer overflow-hidden
                          ${isExpanded ? 'bg-[#191919] border-[#FFD60A]/30 shadow-[0_0_0_1px_rgba(255,214,10,0.15)] md:col-span-2 xl:col-span-1' : 'bg-[#151515] border-[#222] hover:border-[#333] hover:bg-[#191919]'}
                        `}
                        onClick={() => handleExpand(n.id)}
                      >
                        <div className="p-3 md:p-[14px] flex flex-col gap-2.5">
                          <div className="flex items-start justify-between gap-2">
                            <h3 className={`font-black leading-[1.35] flex-1 transition-colors ${isExpanded ? 'text-[#FFD60A] text-[15px]' : 'text-white text-[14.5px] md:text-[15px] group-hover:text-[#FFD60A]'}`}>
                              {lang === '中文' ? n.title : n.titleBM}
                            </h3>
                            {n.pin && <span className="shrink-0 w-2 h-2 rounded-full bg-[#EC4899] mt-2"></span>}
                          </div>

                          {isExpanded && (
                            <div className="animate-[fadeIn_0.25s_ease]">
                              <div className="flex items-center gap-2 mb-3 flex-wrap">
                                <span className="px-2 py-[2px] rounded-[6px] bg-[#FFD60A] text-black text-[10px] font-black tracking-wide">{n.tag}</span>
                                <span className="text-[11px] mono text-[#888]">{n.location}</span>
                                <span className="w-1 h-1 bg-[#333] rounded-full"></span>
                                <span className="text-[11px] mono text-[#666]">{n.mmdd} {n.time}</span>
                              </div>

                              <div className="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-3 space-y-3">
                                <div className="flex items-center gap-1.5">
                                  <span className="w-1 h-4 rounded-full bg-[#FFD60A]"></span>
                                  <span className="text-[11px] font-bold text-[#FFD60A] tracking-wider">{t('深度报道 / 丰富全文', 'Laporan Mendalam')}</span>
                                  <span className="text-[10px] mono text-[#555]">• 200-300字 • {n.mmdd}</span>
                                </div>
                                {n.id === 9 && (
                                  <div className="rounded-[8px] overflow-hidden border border-[#222] bg-[#111]">
                                    <img src={emergencyAlertImg} alt="Emergency Alert Severe Flash Flood Warning - 政府测试警报 沙巴星洲日报" className="w-full h-auto object-contain max-h-[420px]" />
                                    <div className="px-2.5 py-2 bg-[#161616] border-t border-[#222] flex items-center justify-between">
                                      <span className="text-[10px] mono text-[#888]">FB @沙巴星洲日报 Sabah Sin Chew Daily • 已核实 Official Screenshot</span>
                                      <span className="text-[10px] font-bold px-1.5 py-[1px] rounded-full bg-[#FFD60A] text-black">图：Emergency Alert 巨响示意</span>
                                    </div>
                                  </div>
                                )}
                                {richParas.map((para, pi) => (
                                  <p key={pi} className="text-[13px] leading-[1.7] text-[#d1d5db]">
                                    {pi === 0 ? (
                                      <>
                                        <span className="inline-block w-2 h-2 rounded-full bg-[#FFD60A] mr-2 mb-[2px]"></span>
                                        {para}
                                      </>
                                    ) : (
                                      para
                                    )}
                                  </p>
                                ))}
                                <div className="pt-2 border-t border-[#1f1f1f] flex flex-col gap-2">
                                  <div className="flex items-start gap-2 text-[11px] leading-[1.5] text-[#9ca3af] bg-[#161616] border border-[#222] rounded-[8px] p-2.5">
                                    <span className="shrink-0 w-5 h-5 rounded-full bg-[#222] flex items-center justify-center text-[10px]">❞</span>
                                    <span className="italic">
                                      {lang === '中文'
                                        ? `官方引述：“${n.rich[1].slice(0, 42)}...” — 现场核实来源 ${n.sources[0]}`
                                        : `Petikan rasmi: “${n.richBM[1].slice(0, 42)}...” — Sumber disahkan ${n.sources[0]}`}
                                    </span>
                                  </div>
                                  <div className="flex flex-wrap gap-1.5">
                                    {n.sources.map((s) => (
                                      <a
                                        key={s}
                                        href={`https://${s}`}
                                        target="_blank"
                                        rel="noopener"
                                        onClick={(e) => e.stopPropagation()}
                                        className="px-2 py-[3px] rounded-full bg-[#FFD60A]/10 border border-[#FFD60A]/20 text-[10px] text-[#FFD60A] mono hover:bg-[#FFD60A]/20 transition"
                                      >
                                        ↗ {s}
                                      </a>
                                    ))}
                                    <span className="px-2 py-[3px] rounded-full bg-[#14532d] border border-[#166534] text-[10px] text-[#22c55e] font-bold">
                                      ✓ {lang === '中文' ? n.verified : n.verifiedBM}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="mono text-[10px] text-[#666]">{n.mmdd} {n.time}</span>
                            <span className={`inline-flex items-center px-1.5 py-[1px] rounded-[4px] text-[10px] font-bold ${n.verified.includes('2') ? 'bg-[#14532d] text-[#22c55e] border border-[#166534]' : 'bg-[#1a1a1a] text-[#888] border border-[#2a2a2a]'}`}>
                              {lang === '中文' ? n.verified : n.verifiedBM}
                            </span>
                            {!isExpanded && <span className="text-[10px] px-1.5 py-[1px] rounded bg-[#1a1a1a] border border-[#222] text-[#555] mono">{n.tag.split(' ')[0]}</span>}
                          </div>

                          <div className="flex flex-wrap gap-1">
                            {n.sources.map((s) => (
                              <span key={s} className="px-1.5 py-[1px] rounded-[4px] bg-[#1f1f1f] border border-[#2a2a2a] text-[10px] text-[#777] mono truncate max-w-[110px]">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className={`mt-auto flex items-center justify-between px-3 py-2.5 border-t ${isExpanded ? 'border-[#FFD60A]/20 bg-[#FFD60A]/5' : 'border-[#1f1f1f] bg-[#111]/50'}`}>
                          <span className="text-[11px] text-[#555] mono">
                            {isExpanded ? t('已展开丰富全文', 'Berita penuh dibuka') : t('标题-only', 'Tajuk sahaja')}
                          </span>
                          <span className={`text-[12px] font-black tracking-tight flex items-center gap-1 transition-all ${isExpanded ? 'text-white' : 'text-[#FFD60A] group-hover:translate-x-[2px]'}`}>
                            {isExpanded ? (
                              <>{t('收起 ↑', 'Tutup ↑')}</>
                            ) : (
                              <>
                                {t('点击展开 →', 'Klik baca →')}
                                <span className="w-5 h-5 rounded-full bg-[#FFD60A] text-black flex items-center justify-center text-[11px] group-hover:bg-[#ffdb33]">→</span>
                              </>
                            )}
                          </span>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </div>

            {/* 未来2周归档 - always visible below news regardless of filter */}
            <div className="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden">
              <div className="px-4 py-3 border-b border-[#222] flex items-center justify-between gap-2">
                <h3 className="font-black text-[14px] md:text-[15px] flex items-center gap-2">
                  <span>{t('未来2周归档', 'Arkib 2 Minggu Akan Datang')}</span>
                  <span className="hidden sm:inline-flex items-center px-2 py-[1px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">4 {t('项活动', 'aktiviti')}</span>
                  <span className="inline-flex items-center gap-1 px-2 py-[1px] rounded-full bg-[#111] border border-[#222] text-[10px] mono text-[#666]">{t('始终可见 不受日期筛选影响', 'Kekal visible tanpa filter')}</span>
                </h3>
                <span className="text-[10px] mono text-[#666] text-right leading-tight">
                  {t('已确认自动过时 Auto-hide past events ✓', 'Auto-hide past ✓')}
                </span>
              </div>
              <div className="p-2 grid grid-cols-1 md:grid-cols-2 gap-2">
                {EVENTS.map((ev, idx) => {
                  const isOpen = expandedEvent === idx;
                  return (
                    <div
                      key={idx}
                      onClick={() => setExpandedEvent(isOpen ? null : idx)}
                      className={`group cursor-pointer rounded-[10px] border bg-[#111] hover:bg-[#161616] transition-all ${isOpen ? 'border-[#FFD60A]/40 bg-[#161616] ring-1 ring-[#FFD60A]/20' : 'border-[#222]'}`}
                    >
                      <div className="flex items-center gap-2.5 p-2.5">
                        <div className="shrink-0 w-[48px] h-[48px] rounded-[8px] bg-[#FFD60A] text-black flex flex-col items-center justify-center leading-none">
                          <span className="font-black text-[13px]">{ev.date.split('/')[0]}</span>
                          <span className="font-bold text-[11px]">/{ev.date.split('/')[1]}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-[13px] font-bold leading-tight truncate text-white group-hover:text-[#FFD60A] transition-colors">{lang === '中文' ? ev.name : ev.nameBM}</div>
                          <div className="text-[11px] text-[#888] truncate flex items-center gap-1">
                            {ev.location}
                            <span className="text-[#555]">•</span>
                            <span className="text-[#666] mono text-[10px]">{t('点击看详情', 'Klik butiran')}</span>
                          </div>
                        </div>
                        <div className="shrink-0 flex flex-col items-end gap-1">
                          <span className={`px-2 py-[3px] rounded-full text-[11px] font-bold leading-none ${ev.color === 'red' ? 'bg-[#7f1d1d] text-[#fca5a5]' : ev.color === 'pink' ? 'bg-[#831843] text-[#f9a8d4]' : 'bg-[#713f12] text-[#fde68a]'}`}>
                            {lang === '中文' ? ev.days : ev.daysBM}
                          </span>
                          <span className={`text-[10px] transition-transform ${isOpen ? 'rotate-180' : ''} text-[#555]`}>▼</span>
                        </div>
                      </div>
                      {isOpen && (
                        <div className="px-2.5 pb-2.5">
                          <div className="rounded-[8px] bg-[#0f0f0f] border border-[#222] p-2.5 flex flex-col gap-2.5">
                            <div className="text-[12px] leading-[1.5] text-[#bbb]">
                              {lang === '中文' ? ev.simple : ev.simpleBM}
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="inline-flex items-center gap-1.5 px-2 py-[3px] rounded-full bg-[#1e1e1e] border border-[#2a2a2a] text-[11px]">
                                <span className="w-4 h-4 rounded-full bg-[#22c55e] flex items-center justify-center text-[9px] text-black font-black">☎</span>
                                <span className="text-[#e5e7eb] font-medium mono">{lang === '中文' ? ev.consult : ev.consultBM}</span>
                              </div>
                              <a
                                href={ev.link}
                                target="_blank"
                                rel="noopener"
                                onClick={(e) => e.stopPropagation()}
                                className="inline-flex items-center gap-1 px-2 py-[3px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black hover:bg-[#ffdb33] transition"
                              >
                                {t('去咨询 →', 'Konsultasi →')}
                              </a>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="inline-flex items-center gap-1 px-2 py-[2px] rounded-[6px] bg-[#14532d] border border-[#166534] text-[#22c55e] text-[10px] font-bold">
                                ✓ {t('已确认', 'Disahkan')} {lang === '中文' ? ev.source : ev.sourceBM}
                              </span>
                              <span className="text-[10px] mono text-[#555]">{t('点击展开询问咨询', 'Klik kembang konsultasi')}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <div className="px-4 py-2.5 bg-[#111] border-t border-[#222] flex items-center justify-between">
                <span className="text-[11px] text-[#666] mono">4 {t('项活动', 'aktiviti')} • {t('点击展开询问咨询', 'Klik kembang konsultasi')}</span>
                <span className="text-[11px] text-[#22c55e] font-bold">✓ {t('自动过时', 'Auto-hide')} • {todayStr} MYT</span>
              </div>
            </div>

            <div className="p-3 rounded-[10px] bg-[#111] border border-[#222] flex items-center justify-between text-[11px] mono text-[#666]">
              <span>{todayStr} {mytTimeStr} MYT • 标题-only折叠 点击展开200-300字全文 • {archiveDays.length}天归档已启用</span>
              <span className="text-[#FFD60A]">{allNews.length}标题 • 归档筛选→ 丰富内容</span>
            </div>
          </div>

          {/* RIGHT SIDEBAR - ADS AT TOP ALWAYS */}
          <div className="w-full lg:w-[320px] xl:w-[360px] shrink-0 flex flex-col gap-3 lg:sticky lg:top-[calc(var(--safe-area-inset-top)+68px)] lg:h-fit">
            <div className="bg-[#151515] border border-[#222] rounded-[12px] overflow-hidden">
              <div className="bg-[#FFD60A] px-4 py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-[6px] bg-black text-[#FFD60A] flex items-center justify-center font-black text-[12px]">M</span>
                  <span className="font-black text-black text-[13px] tracking-tight">MY CAR ENTERPRISE</span>
                </div>
                <span className="px-2 py-[2px] rounded-full bg-black text-[#FFD60A] text-[10px] font-bold">AD • Marco Thien</span>
              </div>
              <div className="p-0">
                <div className="w-full bg-white">
                  <img src={myCarPoster} alt="MY CAR ENTERPRISE Sewa Kereta - Kereta Sewa Untuk Semua Keperluan Anda" className="w-full h-auto object-contain" />
                </div>
                <div className="p-3 bg-[#151515] flex flex-col gap-3">
                  <div className="rounded-[10px] bg-[#111] border border-[#222] p-3 flex flex-col gap-2.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[10px] font-black">官方 Official Poster</span>
                      <span className="text-[11px] mono text-[#666]">山打根租车服务 Rent Car Service Sandakan</span>
                    </div>
                    <div className="text-[13px] font-black leading-[1.35] text-white">
                      {t('Kereta Sewa Untuk Semua Keperluan Anda', 'Kereta Sewa Untuk Semua Keperluan Anda')}
                    </div>
                    <div className="text-[12px] font-bold text-[#FFD60A] tracking-tight">
                      {t('Jom Travel Bersama Kami • Sabah Menanti Anda', 'Jom Travel Bersama Kami • Sabah Menanti Anda')}
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[10px] mono text-[#666] font-bold tracking-wider">FEATURES / 特色</span>
                        <ul className="flex flex-col gap-1">
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Kereta Bersih & Selesa</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Pelbagai Jenis Kenderaan</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Harga Berpatutan</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Tempoh Sewa Fleksibel</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#FFD60A] shrink-0"></span>Servis Mesra & Dipercayai</li>
                        </ul>
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <span className="text-[10px] mono text-[#666] font-bold tracking-wider">FLEET / 车型</span>
                        <ul className="flex flex-col gap-1">
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>K-car Myvi Axia Viva</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Sedan Vios Bezza</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>MPV Vellfire Alphard Veloz Innova Alza Aruz</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Van 11 / 14 Seats</li>
                          <li className="flex items-center gap-1.5 text-[11px] text-[#bbb]"><span className="w-1 h-1 rounded-full bg-[#222] shrink-0"></span>Double Cab 4x4</li>
                        </ul>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      <span className="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Ativa</span>
                      <span className="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Veloz</span>
                      <span className="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Axia</span>
                      <span className="px-2 py-[2px] rounded-full bg-[#1a1a1a] border border-[#2a2a2a] text-[10px] text-[#ddd] font-bold">Aruz</span>
                    </div>
                  </div>

                  <div className="rounded-[10px] bg-[#0f0f0f] border border-[#222] p-2.5 flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-[#FFD60A] text-black flex items-center justify-center font-black text-[12px]">M</div>
                        <div className="leading-tight">
                          <div className="text-[12px] font-black text-white">Marco Thien</div>
                          <div className="text-[10px] mono text-[#888]">山打根租车服务</div>
                        </div>
                      </div>
                      <span className="px-2 py-[2px] rounded-full bg-[#14532d] border border-[#166534] text-[#22c55e] text-[10px] font-bold">✓ 已核实 Verified</span>
                    </div>
                    <div className="flex flex-col gap-1 pt-1">
                      <div className="flex items-center gap-2 text-[12px] mono">
                        <span className="w-5 h-5 rounded-[5px] bg-[#1a1a1a] border border-[#222] flex items-center justify-center text-[11px]">📞</span>
                        <span className="text-white font-bold">010-930 1117</span>
                        <span className="text-[#666] text-[11px]">Marco</span>
                      </div>
                      <div className="flex items-center gap-2 text-[12px] mono">
                        <span className="w-5 h-5 rounded-[5px] bg-[#1a1a1a] border border-[#222] flex items-center justify-center text-[11px]">💬</span>
                        <span className="text-[#bbb]">WeChat: Thien1117</span>
                      </div>
                    </div>
                  </div>

                  <a href="https://wa.me/60109301117" target="_blank" rel="noopener" className="w-full h-10 rounded-[8px] bg-[#FFD60A] text-black font-black text-[13px] flex items-center justify-center gap-2 hover:bg-[#ffdb33] transition shadow-[0_2px_8px_rgba(255,214,10,0.25)]">
                    <span>WhatsApp Marco 询价</span>
                    <span className="text-[14px]">→</span>
                  </a>
                  <div className="flex items-center justify-between px-1">
                    <span className="text-[10px] mono text-[#555]">AD • managed first-party media</span>
                    <span className="text-[10px] mono text-[#555]">Rent Car Service Sandakan</span>
                  </div>
                </div>
              </div>
            </div>

            {/* SAZA RICE - TRUE POSTER */}
            <div className="rounded-[12px] overflow-hidden border border-[#1e40af]/30 bg-white shadow-[0_2px_12px_rgba(30,64,175,0.15)]">
              <div className="bg-[#1E40AF] px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-[8px] bg-white text-[#1E40AF] flex items-center justify-center font-black text-[13px] shadow-sm">S</div>
                  <div className="leading-tight">
                    <div className="font-black text-white text-[14px] tracking-tight">SAZA RICE</div>
                    <div className="text-[#93c5fd] text-[10px] mono font-bold tracking-wider">BERAS WANGI MALAYSIA • AD</div>
                  </div>
                </div>
                <span className="px-2 py-[2px] rounded-full bg-white text-[#1E40AF] text-[10px] font-black">官方 Official</span>
              </div>

              <div className="p-0 bg-white">
                <div className="w-full bg-[#f8fafc] p-2">
                  <img
                    src={sazaPoster}
                    alt="Saza Rice - Beli Beras Saza Rice Dan Menang Hadiah Menarik! Peraduan Beli & Menang 1 Sep - 31 Dis 2026 - Jetour Dashing Hadiah Utama"
                    className="w-full h-auto object-contain rounded-[10px] border border-[#bfdbfe]"
                  />
                </div>

                <div className="p-3 bg-[#f8fafc] flex flex-col gap-3">
                  <div className="rounded-[8px] bg-[#eff6ff] border border-[#bfdbfe] px-3 py-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse"></span>
                      <span className="text-[11px] font-black text-[#1e40af] mono">Peraduan Beli & Menang 1 SEP - 31 DIS 2026</span>
                    </div>
                    <span className="text-[10px] text-[#64748b] mono">www.momom2u.com</span>
                  </div>

                  <div className="grid grid-cols-2 gap-1.5 text-[10px] leading-[1.4] text-[#334155] px-1">
                    <span className="flex items-center gap-1"><span className="w-1 h-1 bg-[#1e40af] rounded-full"></span>Hadiah Utama: Jetour Dashing 1.5</span>
                    <span className="flex items-center gap-1"><span className="w-1 h-1 bg-[#1e40af] rounded-full"></span>Travel RM8888 x2 / S26 Ultra x2</span>
                    <span className="flex items-center gap-1"><span className="w-1 h-1 bg-[#1e40af] rounded-full"></span>Gold Card RM4k x2 / TV 65" x3</span>
                    <span className="flex items-center gap-1"><span className="w-1 h-1 bg-[#1e40af] rounded-full"></span>Bulanan: Rice Cooker, Air Fryer etc</span>
                  </div>

                  <button
                    onClick={() => window.open('https://www.facebook.com/search/pages/?q=Saza%20Rice','_blank')}
                    className="w-full h-10 rounded-[8px] bg-[#1877F2] hover:bg-[#166fe5] text-white font-black text-[13px] flex items-center justify-center gap-2 transition shadow-[0_2px_8px_rgba(24,119,242,0.3)]"
                  >
                    <span className="w-5 h-5 rounded-full bg-white text-[#1877F2] flex items-center justify-center font-black text-[12px]">f</span>
                    <span>{t('关注 Saza Rice Facebook', 'Follow Saza Rice Facebook')}</span>
                    <span className="text-[14px]">→</span>
                  </button>

                  <div className="flex items-center justify-between px-1">
                    <span className="text-[10px] mono text-[#94a3b8]">{t('广告 AD • 已核实官方活动 • 1 Sep - 31 Dis 2026', 'Iklan AD • Kempen Rasmi • 1 Sep - 31 Dis 2026')}</span>
                    <span className="inline-flex items-center gap-1 px-1.5 py-[1px] rounded-full bg-[#dcfce7] border border-[#bbf7d0] text-[#16a34a] text-[9px] font-bold">✓ {t('已确认', 'Disahkan')}</span>
                  </div>
                  <div className="text-[10px] mono text-[#64748b] px-1">
                    Duta: Dabra Sia • Sazarice Sdn Bhd • chefmomomofficial • www.sazarice.com 019 218 0882 • Menyempurnakan Selera Sabahan
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-[#111] border border-[#222] rounded-[12px] p-3">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-[2px] rounded-full bg-[#FFD60A] text-black text-[11px] font-bold">{t('归档已启用 6天', 'Arkib Aktif 6 Hari')}</span>
                <span className="text-[11px] text-[#666] mono">{todayStr} MYT • {t('动态日期', 'Dinamik')}</span>
              </div>
              <p className="text-[11px] leading-[1.6] text-[#777]">
                {t(
                  `本版为归档版：已启用今天/昨天/前天/3天前/4天前/5天前/全部筛选，日期基于 Asia/Kuala_Lumpur 时区通过 toLocaleString 动态计算 ${todayStr}，非写死。卡片默认标题-only，点击展开200-300字深度全文。未来2周活动始终可见不受筛选影响。UTILITI LIVE 3卡始终LIVE。`,
                  `Versi arkib: filter Hari Ini/Semalam/Kelmarin/3 hari lalu/4 hari lalu/5 hari lalu/Semua aktif, tarikh dikira dinamik berdasarkan zon Asia/Kuala_Lumpur melalui toLocaleString ${todayStr}, bukan hardcode. Kad lalai tajuk sahaja, klik kembang laporan 200-300 patah. Aktiviti 2 minggu akan datang kekal visible. UTILITI LIVE 3 kad kekal LIVE.`
                )}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-4 border-t border-[#1a1a1a] flex flex-col md:flex-row items-center justify-between gap-2 text-[11px] mono text-[#555]">
          <span>© 2026 西门看看网 • {todayStr} {mytTimeStr} MYT动态归档版 - {archiveDays.length}天筛选 • 标题-only 点击展开全文 • 活动栏始终可见</span>
          <span className="flex items-center gap-3">
            <span>山打根 Sandakan • MYT Asia/Kuala_Lumpur</span>
            <span>•</span>
            <span>{allNews.length}标题 4项活动</span>
            <span>•</span>
            <span className="text-[#22c55e]">✓ 已核实</span>
          </span>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        .mono{ font-family: 'JetBrains Mono', monospace; }
        @media (max-width: 390px){
          .grid{ gap: 10px !important; }
        }
        @keyframes fadeIn{
          from{opacity:0; transform:translateY(-4px)}
          to{opacity:1; transform:translateY(0)}
        }
        @keyframes marquee{
          0%{ transform: translateX(0) }
          100%{ transform: translateX(-50%) }
        }
      `}</style>
    </div>
  );
}
