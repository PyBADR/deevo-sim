"""
Impact Observatory — Entity Graph Registry

76 real GCC entity nodes + 190 weighted causal edges.
Ported from @deevo/gcc-knowledge-graph TypeScript package.
"""

from typing import Optional


NODES: list[dict] = [
    {"id":"geo_sa","label":"Saudi Arabia","label_ar":"السعودية","layer":"geography","type":"Region","lat":24.7136,"lng":46.6753,"weight":0.95,"sensitivity":0.3,"damping_factor":0.02,"value":0.95},
    {"id":"geo_uae","label":"UAE","label_ar":"الإمارات","layer":"geography","type":"Region","lat":25.2048,"lng":55.2708,"weight":0.9,"sensitivity":0.3,"damping_factor":0.02,"value":0.9},
    {"id":"geo_kw","label":"Kuwait","label_ar":"الكويت","layer":"geography","type":"Region","lat":29.3759,"lng":47.9774,"weight":0.75,"sensitivity":0.35,"damping_factor":0.03,"value":0.75},
    {"id":"geo_qa","label":"Qatar","label_ar":"قطر","layer":"geography","type":"Region","lat":25.2854,"lng":51.531,"weight":0.8,"sensitivity":0.3,"damping_factor":0.02,"value":0.8},
    {"id":"geo_om","label":"Oman","label_ar":"عُمان","layer":"geography","type":"Region","lat":23.588,"lng":58.3829,"weight":0.65,"sensitivity":0.4,"damping_factor":0.04,"value":0.65},
    {"id":"geo_bh","label":"Bahrain","label_ar":"البحرين","layer":"geography","type":"Region","lat":26.0667,"lng":50.5577,"weight":0.6,"sensitivity":0.45,"damping_factor":0.04,"value":0.6},
    {"id":"geo_hormuz","label":"Strait of Hormuz","label_ar":"مضيق هرمز","layer":"geography","type":"Event","lat":26.5944,"lng":56.4667,"weight":0.98,"sensitivity":0.1,"damping_factor":0.01,"value":0.98},
    {"id":"inf_ruh","label":"RUH Airport","label_ar":"مطار الرياض","layer":"infrastructure","type":"Organization","lat":24.9578,"lng":46.6989,"weight":0.8,"sensitivity":0.5,"damping_factor":0.05,"value":0.8},
    {"id":"inf_jed","label":"JED Airport","label_ar":"مطار جدة","layer":"infrastructure","type":"Organization","lat":21.6796,"lng":39.1565,"weight":0.85,"sensitivity":0.5,"damping_factor":0.05,"value":0.85},
    {"id":"inf_dmm","label":"DMM Airport","label_ar":"مطار الدمام","layer":"infrastructure","type":"Organization","lat":26.4712,"lng":49.7979,"weight":0.7,"sensitivity":0.55,"damping_factor":0.06,"value":0.7},
    {"id":"inf_dxb","label":"DXB Airport","label_ar":"مطار دبي","layer":"infrastructure","type":"Organization","lat":25.2532,"lng":55.3657,"weight":0.88,"sensitivity":0.5,"damping_factor":0.05,"value":0.88},
    {"id":"inf_auh","label":"AUH Airport","label_ar":"مطار أبوظبي","layer":"infrastructure","type":"Organization","lat":24.433,"lng":54.6511,"weight":0.82,"sensitivity":0.5,"damping_factor":0.05,"value":0.82},
    {"id":"inf_doh","label":"DOH Airport","label_ar":"مطار الدوحة","layer":"infrastructure","type":"Organization","lat":25.2731,"lng":51.6081,"weight":0.75,"sensitivity":0.5,"damping_factor":0.05,"value":0.75},
    {"id":"inf_kwi","label":"KWI Airport","label_ar":"مطار الكويت","layer":"infrastructure","type":"Organization","lat":29.2266,"lng":47.9689,"weight":0.65,"sensitivity":0.55,"damping_factor":0.06,"value":0.65},
    {"id":"inf_bah","label":"BAH Airport","label_ar":"مطار البحرين","layer":"infrastructure","type":"Organization","lat":26.2708,"lng":50.6336,"weight":0.6,"sensitivity":0.55,"damping_factor":0.06,"value":0.6},
    {"id":"inf_mct","label":"MCT Airport","label_ar":"مطار مسقط","layer":"infrastructure","type":"Organization","lat":23.5933,"lng":58.2844,"weight":0.62,"sensitivity":0.55,"damping_factor":0.06,"value":0.62},
    {"id":"inf_jebel","label":"Jebel Ali Port","label_ar":"ميناء جبل علي","layer":"infrastructure","type":"Organization","lat":24.9857,"lng":55.0272,"weight":0.92,"sensitivity":0.6,"damping_factor":0.04,"value":0.92},
    {"id":"inf_dammam","label":"Dammam Port","label_ar":"ميناء الدمام","layer":"infrastructure","type":"Organization","lat":26.4473,"lng":50.1014,"weight":0.78,"sensitivity":0.6,"damping_factor":0.05,"value":0.78},
    {"id":"inf_doha_p","label":"Doha Port","label_ar":"ميناء الدوحة","layer":"infrastructure","type":"Organization","lat":25.296,"lng":51.5488,"weight":0.6,"sensitivity":0.55,"damping_factor":0.06,"value":0.6},
    {"id":"inf_hamad","label":"Hamad Port","label_ar":"ميناء حمد","layer":"infrastructure","type":"Organization","lat":25.0147,"lng":51.6014,"weight":0.75,"sensitivity":0.55,"damping_factor":0.05,"value":0.75},
    {"id":"inf_khalifa","label":"Khalifa Port","label_ar":"ميناء خليفة","layer":"infrastructure","type":"Organization","lat":24.8125,"lng":54.6486,"weight":0.8,"sensitivity":0.55,"damping_factor":0.05,"value":0.8},
    {"id":"inf_shuwaikh","label":"Shuwaikh Port","label_ar":"ميناء الشويخ","layer":"infrastructure","type":"Organization","lat":29.35,"lng":47.92,"weight":0.65,"sensitivity":0.55,"damping_factor":0.06,"value":0.65},
    {"id":"inf_sohar","label":"Sohar Port","label_ar":"ميناء صحار","layer":"infrastructure","type":"Organization","lat":24.34,"lng":56.74,"weight":0.68,"sensitivity":0.55,"damping_factor":0.06,"value":0.68},
    {"id":"inf_desal","label":"Desalination Plants","label_ar":"محطات التحلية","layer":"infrastructure","type":"Organization","lat":25.6,"lng":55.5,"weight":0.82,"sensitivity":0.55,"damping_factor":0.04,"value":0.82},
    {"id":"inf_power","label":"Power Grid","label_ar":"شبكة الكهرباء","layer":"infrastructure","type":"Organization","lat":24.92,"lng":46.75,"weight":0.85,"sensitivity":0.5,"damping_factor":0.03,"value":0.85},
    {"id":"inf_telecom","label":"GCC Telecom","label_ar":"الاتصالات الخليجية","layer":"infrastructure","type":"Organization","lat":24.71,"lng":54,"weight":0.8,"sensitivity":0.45,"damping_factor":0.04,"value":0.8},
    {"id":"gov_transport","label":"Min. of Transport","label_ar":"وزارة النقل","layer":"infrastructure","type":"Ministry","lat":24.68,"lng":46.72,"weight":0.8,"sensitivity":0.35,"damping_factor":0.03,"value":0.8},
    {"id":"gov_water","label":"Min. of Water & Elec.","label_ar":"وزارة المياه والكهرباء","layer":"infrastructure","type":"Ministry","lat":24.69,"lng":46.73,"weight":0.82,"sensitivity":0.4,"damping_factor":0.03,"value":0.82},
    {"id":"inf_airport_throughput","label":"Airport Throughput","label_ar":"حركة المطارات","layer":"infrastructure","type":"Topic","lat":25.15,"lng":55.2,"weight":0.82,"sensitivity":0.7,"damping_factor":0.05,"value":0.82},
    {"id":"eco_oil","label":"Oil Export","label_ar":"صادرات النفط","layer":"economy","type":"Topic","lat":26.3,"lng":50.2,"weight":0.96,"sensitivity":0.7,"damping_factor":0.03,"value":0.96},
    {"id":"eco_aramco","label":"Aramco","label_ar":"أرامكو","layer":"economy","type":"Organization","lat":26.3175,"lng":50.2083,"weight":0.95,"sensitivity":0.5,"damping_factor":0.03,"value":0.95},
    {"id":"eco_adnoc","label":"ADNOC","label_ar":"أدنوك","layer":"economy","type":"Organization","lat":24.4539,"lng":54.3773,"weight":0.88,"sensitivity":0.5,"damping_factor":0.04,"value":0.88},
    {"id":"eco_kpc","label":"KPC","label_ar":"مؤسسة البترول الكويتية","layer":"economy","type":"Organization","lat":29.3375,"lng":48.0013,"weight":0.78,"sensitivity":0.55,"damping_factor":0.04,"value":0.78},
    {"id":"eco_shipping","label":"Shipping Cost","label_ar":"تكلفة الشحن","layer":"economy","type":"Topic","lat":25,"lng":55.1,"weight":0.85,"sensitivity":0.65,"damping_factor":0.05,"value":0.85},
    {"id":"eco_aviation","label":"Aviation Fuel Cost","label_ar":"تكلفة وقود الطيران","layer":"economy","type":"Topic","lat":25.0657,"lng":55.1713,"weight":0.82,"sensitivity":0.6,"damping_factor":0.05,"value":0.82},
    {"id":"eco_fuel","label":"Fuel Cost","label_ar":"تكلفة الوقود","layer":"economy","type":"Topic","lat":24.47,"lng":54.37,"weight":0.88,"sensitivity":0.7,"damping_factor":0.04,"value":0.88},
    {"id":"eco_gdp","label":"GCC GDP","label_ar":"الناتج المحلي الخليجي","layer":"economy","type":"Topic","lat":24.47,"lng":49,"weight":0.9,"sensitivity":0.4,"damping_factor":0.02,"value":0.9},
    {"id":"eco_tourism","label":"Tourism Revenue","label_ar":"إيرادات السياحة","layer":"economy","type":"Topic","lat":25.197,"lng":55.2744,"weight":0.78,"sensitivity":0.65,"damping_factor":0.05,"value":0.78},
    {"id":"eco_food","label":"Food Security","label_ar":"الأمن الغذائي","layer":"economy","type":"Topic","lat":25.05,"lng":51,"weight":0.88,"sensitivity":0.7,"damping_factor":0.05,"value":0.88},
    {"id":"gov_energy","label":"Min. of Energy","label_ar":"وزارة الطاقة","layer":"economy","type":"Ministry","lat":24.7,"lng":46.7,"weight":0.9,"sensitivity":0.3,"damping_factor":0.02,"value":0.9},
    {"id":"gov_tourism","label":"Min. of Tourism","label_ar":"وزارة السياحة","layer":"economy","type":"Ministry","lat":24.75,"lng":46.71,"weight":0.75,"sensitivity":0.4,"damping_factor":0.03,"value":0.75},
    {"id":"eco_telecom","label":"Telecom Sector","label_ar":"قطاع الاتصالات","layer":"economy","type":"Topic","lat":24.7,"lng":54.1,"weight":0.78,"sensitivity":0.5,"damping_factor":0.04,"value":0.78},
    {"id":"eco_logistics","label":"Logistics Hub","label_ar":"المركز اللوجستي","layer":"economy","type":"Topic","lat":25.01,"lng":55.08,"weight":0.8,"sensitivity":0.6,"damping_factor":0.05,"value":0.8},
    {"id":"eco_saudia","label":"Saudia Airlines","label_ar":"الخطوط السعودية","layer":"economy","type":"Organization","lat":24.96,"lng":46.7,"weight":0.75,"sensitivity":0.65,"damping_factor":0.05,"value":0.75},
    {"id":"eco_emirates","label":"Emirates","label_ar":"طيران الإمارات","layer":"economy","type":"Organization","lat":25.25,"lng":55.37,"weight":0.8,"sensitivity":0.6,"damping_factor":0.05,"value":0.8},
    {"id":"eco_qatar_aw","label":"Qatar Airways","label_ar":"الخطوط القطرية","layer":"economy","type":"Organization","lat":25.27,"lng":51.57,"weight":0.78,"sensitivity":0.6,"damping_factor":0.05,"value":0.78},
    {"id":"eco_kw_airways","label":"Kuwait Airways","label_ar":"الخطوط الكويتية","layer":"economy","type":"Organization","lat":29.23,"lng":47.97,"weight":0.65,"sensitivity":0.6,"damping_factor":0.05,"value":0.65},
    {"id":"eco_gulf_air","label":"Gulf Air","label_ar":"طيران الخليج","layer":"economy","type":"Organization","lat":26.27,"lng":50.63,"weight":0.6,"sensitivity":0.6,"damping_factor":0.05,"value":0.6},
    {"id":"eco_oman_air","label":"Oman Air","label_ar":"الطيران العماني","layer":"economy","type":"Organization","lat":23.59,"lng":58.28,"weight":0.58,"sensitivity":0.6,"damping_factor":0.05,"value":0.58},
    {"id":"eco_av_stress","label":"Aviation Sector Stress","label_ar":"ضغط قطاع الطيران","layer":"economy","type":"Topic","lat":25.1,"lng":55.15,"weight":0.8,"sensitivity":0.7,"damping_factor":0.05,"value":0.8},
    {"id":"fin_sama","label":"SAMA","label_ar":"مؤسسة النقد","layer":"finance","type":"Organization","lat":24.6918,"lng":46.6855,"weight":0.92,"sensitivity":0.35,"damping_factor":0.02,"value":0.92},
    {"id":"fin_uae_cb","label":"UAE Central Bank","label_ar":"مصرف الإمارات المركزي","layer":"finance","type":"Organization","lat":24.4872,"lng":54.3613,"weight":0.88,"sensitivity":0.35,"damping_factor":0.02,"value":0.88},
    {"id":"fin_kw_cb","label":"Kuwait Central Bank","label_ar":"بنك الكويت المركزي","layer":"finance","type":"Organization","lat":29.3759,"lng":47.985,"weight":0.75,"sensitivity":0.4,"damping_factor":0.03,"value":0.75},
    {"id":"fin_qa_cb","label":"Qatar Central Bank","label_ar":"مصرف قطر المركزي","layer":"finance","type":"Organization","lat":25.2867,"lng":51.5333,"weight":0.78,"sensitivity":0.35,"damping_factor":0.02,"value":0.78},
    {"id":"fin_om_cb","label":"Oman Central Bank","label_ar":"البنك المركزي العماني","layer":"finance","type":"Organization","lat":23.59,"lng":58.38,"weight":0.65,"sensitivity":0.4,"damping_factor":0.03,"value":0.65},
    {"id":"fin_bh_cb","label":"Bahrain Central Bank","label_ar":"مصرف البحرين المركزي","layer":"finance","type":"Organization","lat":26.22,"lng":50.59,"weight":0.68,"sensitivity":0.4,"damping_factor":0.03,"value":0.68},
    {"id":"fin_banking","label":"Commercial Banks","label_ar":"البنوك التجارية","layer":"finance","type":"Organization","lat":24.72,"lng":46.69,"weight":0.88,"sensitivity":0.55,"damping_factor":0.04,"value":0.88},
    {"id":"fin_insurers","label":"Insurance Risk","label_ar":"مخاطر التأمين","layer":"finance","type":"Organization","lat":24.75,"lng":46.72,"weight":0.8,"sensitivity":0.7,"damping_factor":0.06,"value":0.8},
    {"id":"fin_reinsure","label":"Reinsurers","label_ar":"إعادة التأمين","layer":"finance","type":"Organization","lat":25.18,"lng":55.28,"weight":0.75,"sensitivity":0.65,"damping_factor":0.05,"value":0.75},
    {"id":"fin_ins_risk","label":"Insurance Risk","label_ar":"مخاطر التأمين","layer":"finance","type":"Topic","lat":25.22,"lng":55.26,"weight":0.82,"sensitivity":0.7,"damping_factor":0.06,"value":0.82},
    {"id":"fin_tadawul","label":"Tadawul Exchange","label_ar":"تداول","layer":"finance","type":"Organization","lat":24.69,"lng":46.69,"weight":0.85,"sensitivity":0.6,"damping_factor":0.04,"value":0.85},
    {"id":"gov_finance","label":"Min. of Finance","label_ar":"وزارة المالية","layer":"finance","type":"Ministry","lat":24.685,"lng":46.68,"weight":0.88,"sensitivity":0.3,"damping_factor":0.02,"value":0.88},
    {"id":"soc_citizens","label":"Citizens","label_ar":"المواطنون","layer":"society","type":"Person","lat":24.7,"lng":46.7,"weight":0.85,"sensitivity":0.6,"damping_factor":0.06,"value":0.85},
    {"id":"soc_expats","label":"Expatriate Workers","label_ar":"العمالة الوافدة","layer":"society","type":"Person","lat":25.2,"lng":55.27,"weight":0.8,"sensitivity":0.65,"damping_factor":0.06,"value":0.8},
    {"id":"soc_travelers","label":"Travelers","label_ar":"المسافرون","layer":"society","type":"Person","lat":25.2,"lng":55.3,"weight":0.7,"sensitivity":0.65,"damping_factor":0.07,"value":0.7},
    {"id":"soc_hajj","label":"Hajj & Umrah","label_ar":"الحج والعمرة","layer":"society","type":"Event","lat":21.4225,"lng":39.8262,"weight":0.85,"sensitivity":0.6,"damping_factor":0.05,"value":0.85},
    {"id":"soc_business","label":"Businesses","label_ar":"الشركات","layer":"society","type":"Organization","lat":25.08,"lng":55.14,"weight":0.8,"sensitivity":0.55,"damping_factor":0.05,"value":0.8},
    {"id":"soc_media","label":"Media","label_ar":"الإعلام","layer":"society","type":"Platform","lat":25.2,"lng":55.25,"weight":0.82,"sensitivity":0.5,"damping_factor":0.06,"value":0.82},
    {"id":"soc_social","label":"Social Platforms","label_ar":"المنصات الاجتماعية","layer":"society","type":"Platform","lat":24.72,"lng":46.68,"weight":0.78,"sensitivity":0.4,"damping_factor":0.05,"value":0.78},
    {"id":"soc_travel_d","label":"Travel Demand","label_ar":"الطلب على السفر","layer":"society","type":"Topic","lat":25.25,"lng":55.35,"weight":0.72,"sensitivity":0.7,"damping_factor":0.07,"value":0.72},
    {"id":"soc_ticket","label":"Flight Cost","label_ar":"تكلفة الرحلات","layer":"society","type":"Topic","lat":25.2532,"lng":55.36,"weight":0.68,"sensitivity":0.75,"damping_factor":0.08,"value":0.68},
    {"id":"soc_food_d","label":"Food Demand","label_ar":"الطلب على الغذاء","layer":"society","type":"Topic","lat":25.3,"lng":51.5,"weight":0.82,"sensitivity":0.7,"damping_factor":0.06,"value":0.82},
    {"id":"soc_housing","label":"Housing & Cost of Living","label_ar":"السكن وتكلفة المعيشة","layer":"society","type":"Topic","lat":24.8,"lng":46.8,"weight":0.75,"sensitivity":0.6,"damping_factor":0.06,"value":0.75},
    {"id":"soc_employment","label":"Employment","label_ar":"التوظيف","layer":"society","type":"Topic","lat":24.75,"lng":46.75,"weight":0.8,"sensitivity":0.6,"damping_factor":0.05,"value":0.8},
    {"id":"soc_sentiment","label":"Public Sentiment","label_ar":"المشاعر العامة","layer":"society","type":"Topic","lat":24.8,"lng":46.75,"weight":0.72,"sensitivity":0.65,"damping_factor":0.06,"value":0.72},
    {"id":"soc_stability","label":"Public Stability","label_ar":"الاستقرار العام","layer":"society","type":"Topic","lat":24.65,"lng":46.71,"weight":0.8,"sensitivity":0.4,"damping_factor":0.03,"value":0.8},
]


EDGES: list[dict] = [
    {"id":"e01","source":"geo_hormuz","target":"eco_oil","weight":0.95,"polarity":-1,"label":"disrupts export","label_ar":"يعطّل التصدير"},
    {"id":"e02","source":"eco_oil","target":"eco_aramco","weight":0.9,"polarity":1,"label":"revenue driver","label_ar":"محرك الإيرادات"},
    {"id":"e03","source":"eco_oil","target":"eco_adnoc","weight":0.85,"polarity":1,"label":"revenue driver","label_ar":"محرك الإيرادات"},
    {"id":"e04","source":"eco_oil","target":"eco_kpc","weight":0.8,"polarity":1,"label":"revenue driver","label_ar":"محرك الإيرادات"},
    {"id":"e05","source":"eco_oil","target":"eco_shipping","weight":0.85,"polarity":-1,"label":"oil disruption raises shipping cost","label_ar":"تعطل النفط يرفع تكلفة الشحن"},
    {"id":"e06","source":"eco_oil","target":"eco_fuel","weight":0.88,"polarity":-1,"label":"oil disruption raises fuel price","label_ar":"تعطل النفط يرفع سعر الوقود"},
    {"id":"e07","source":"eco_shipping","target":"inf_jebel","weight":0.85,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e08","source":"eco_shipping","target":"inf_dammam","weight":0.78,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e09","source":"eco_shipping","target":"inf_doha_p","weight":0.6,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e10","source":"eco_shipping","target":"fin_ins_risk","weight":0.8,"polarity":1,"label":"risk exposure","label_ar":"التعرض للمخاطر"},
    {"id":"e67","source":"eco_shipping","target":"inf_hamad","weight":0.7,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e68","source":"eco_shipping","target":"inf_khalifa","weight":0.75,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e69","source":"eco_shipping","target":"inf_shuwaikh","weight":0.55,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e70","source":"eco_shipping","target":"inf_sohar","weight":0.6,"polarity":1,"label":"port traffic","label_ar":"حركة الميناء"},
    {"id":"e11","source":"fin_ins_risk","target":"fin_insurers","weight":0.8,"polarity":1,"label":"premium impact","label_ar":"تأثير الأقساط"},
    {"id":"e12","source":"fin_ins_risk","target":"fin_reinsure","weight":0.75,"polarity":1,"label":"reinsurance cost","label_ar":"تكلفة إعادة التأمين"},
    {"id":"e13","source":"fin_insurers","target":"soc_business","weight":0.65,"polarity":1,"label":"cost pass-through","label_ar":"تمرير التكاليف"},
    {"id":"e136","source":"fin_ins_risk","target":"eco_fuel","weight":0.75,"polarity":1,"label":"insurance surcharge","label_ar":"رسوم التأمين الإضافية"},
    {"id":"e14","source":"eco_fuel","target":"eco_aviation","weight":0.9,"polarity":1,"label":"fuel cost","label_ar":"تكلفة الوقود"},
    {"id":"e15","source":"eco_aviation","target":"soc_ticket","weight":0.85,"polarity":1,"label":"fuel raises flight cost","label_ar":"الوقود يرفع تكلفة الرحلات"},
    {"id":"e137","source":"eco_aviation","target":"eco_tourism","weight":0.7,"polarity":-1,"label":"cost dampens tourism","label_ar":"التكلفة تخفض السياحة"},
    {"id":"e17","source":"soc_travel_d","target":"inf_dxb","weight":0.8,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e18","source":"soc_travel_d","target":"inf_ruh","weight":0.7,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e19","source":"soc_travel_d","target":"inf_kwi","weight":0.55,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e20","source":"soc_travel_d","target":"inf_doh","weight":0.6,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e71","source":"soc_travel_d","target":"inf_jed","weight":0.75,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e72","source":"soc_travel_d","target":"inf_dmm","weight":0.45,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e73","source":"soc_travel_d","target":"inf_auh","weight":0.65,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e74","source":"soc_travel_d","target":"inf_bah","weight":0.4,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e75","source":"soc_travel_d","target":"inf_mct","weight":0.45,"polarity":1,"label":"passenger flow","label_ar":"تدفق الركاب"},
    {"id":"e21","source":"eco_aviation","target":"eco_gdp","weight":0.6,"polarity":-1,"label":"fuel cost drags GDP","label_ar":"تكلفة الوقود تضغط الناتج"},
    {"id":"e22","source":"eco_oil","target":"eco_gdp","weight":0.75,"polarity":1,"label":"oil revenue drives GDP","label_ar":"إيرادات النفط تدعم الناتج"},
    {"id":"e23","source":"eco_shipping","target":"eco_gdp","weight":0.55,"polarity":-1,"label":"shipping cost drags GDP","label_ar":"تكلفة الشحن تضغط الناتج"},
    {"id":"e46","source":"eco_aramco","target":"eco_gdp","weight":0.7,"polarity":1,"label":"revenue","label_ar":"إيرادات"},
    {"id":"e47","source":"eco_adnoc","target":"eco_gdp","weight":0.55,"polarity":1,"label":"revenue","label_ar":"إيرادات"},
    {"id":"e50","source":"eco_tourism","target":"eco_gdp","weight":0.6,"polarity":1,"label":"tourism GDP","label_ar":"ناتج السياحة"},
    {"id":"e76","source":"eco_food","target":"eco_gdp","weight":0.35,"polarity":1,"label":"food sector GDP","label_ar":"ناتج قطاع الغذاء"},
    {"id":"e77","source":"eco_telecom","target":"eco_gdp","weight":0.4,"polarity":1,"label":"telecom GDP","label_ar":"ناتج الاتصالات"},
    {"id":"e78","source":"fin_banking","target":"eco_gdp","weight":0.6,"polarity":1,"label":"credit multiplier","label_ar":"مضاعف الائتمان"},
    {"id":"e24","source":"geo_sa","target":"eco_aramco","weight":0.95,"polarity":1,"label":"national company","label_ar":"شركة وطنية"},
    {"id":"e25","source":"geo_uae","target":"eco_adnoc","weight":0.9,"polarity":1,"label":"national company","label_ar":"شركة وطنية"},
    {"id":"e26","source":"geo_kw","target":"eco_kpc","weight":0.85,"polarity":1,"label":"national company","label_ar":"شركة وطنية"},
    {"id":"e27","source":"geo_sa","target":"inf_ruh","weight":0.8,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e28","source":"geo_uae","target":"inf_dxb","weight":0.85,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e30","source":"geo_sa","target":"inf_dammam","weight":0.78,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e79","source":"geo_sa","target":"inf_jed","weight":0.85,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e80","source":"geo_sa","target":"inf_dmm","weight":0.7,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e81","source":"geo_uae","target":"inf_auh","weight":0.82,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e82","source":"geo_bh","target":"inf_bah","weight":0.75,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e83","source":"geo_om","target":"inf_mct","weight":0.72,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e29","source":"geo_uae","target":"inf_jebel","weight":0.9,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e84","source":"geo_uae","target":"inf_khalifa","weight":0.8,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e85","source":"geo_kw","target":"inf_shuwaikh","weight":0.7,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e86","source":"geo_om","target":"inf_sohar","weight":0.68,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e54","source":"geo_qa","target":"inf_doh","weight":0.8,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e55","source":"geo_qa","target":"inf_doha_p","weight":0.75,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e87","source":"geo_qa","target":"inf_hamad","weight":0.78,"polarity":1,"label":"operates","label_ar":"يشغّل"},
    {"id":"e34","source":"geo_sa","target":"fin_sama","weight":0.85,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e35","source":"geo_uae","target":"fin_uae_cb","weight":0.85,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e36","source":"geo_kw","target":"fin_kw_cb","weight":0.8,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e88","source":"geo_qa","target":"fin_qa_cb","weight":0.8,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e89","source":"geo_om","target":"fin_om_cb","weight":0.75,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e90","source":"geo_bh","target":"fin_bh_cb","weight":0.75,"polarity":1,"label":"governs","label_ar":"يحكم"},
    {"id":"e31","source":"fin_sama","target":"fin_insurers","weight":0.7,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e32","source":"fin_uae_cb","target":"fin_insurers","weight":0.65,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e33","source":"fin_kw_cb","target":"fin_insurers","weight":0.55,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e91","source":"fin_qa_cb","target":"fin_insurers","weight":0.55,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e92","source":"fin_om_cb","target":"fin_insurers","weight":0.45,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e93","source":"fin_bh_cb","target":"fin_insurers","weight":0.5,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e94","source":"fin_sama","target":"fin_banking","weight":0.8,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e95","source":"fin_uae_cb","target":"fin_banking","weight":0.75,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e96","source":"fin_banking","target":"soc_business","weight":0.7,"polarity":1,"label":"business lending","label_ar":"إقراض الشركات"},
    {"id":"e97","source":"fin_banking","target":"soc_housing","weight":0.65,"polarity":1,"label":"mortgage lending","label_ar":"إقراض السكن"},
    {"id":"e98","source":"fin_banking","target":"fin_insurers","weight":0.5,"polarity":1,"label":"bancassurance","label_ar":"التأمين المصرفي"},
    {"id":"e37","source":"soc_citizens","target":"soc_social","weight":0.75,"polarity":1,"label":"expresses via","label_ar":"يعبّر عبر"},
    {"id":"e38","source":"soc_social","target":"soc_media","weight":0.7,"polarity":1,"label":"feeds","label_ar":"يغذي"},
    {"id":"e39","source":"soc_media","target":"soc_citizens","weight":0.6,"polarity":1,"label":"informs","label_ar":"يُعلم"},
    {"id":"e40","source":"eco_fuel","target":"soc_citizens","weight":0.8,"polarity":1,"label":"cost of living","label_ar":"تكلفة المعيشة"},
    {"id":"e41","source":"soc_business","target":"eco_gdp","weight":0.55,"polarity":1,"label":"economic activity","label_ar":"نشاط اقتصادي"},
    {"id":"e42","source":"eco_gdp","target":"soc_citizens","weight":0.5,"polarity":1,"label":"prosperity","label_ar":"الرخاء"},
    {"id":"e48","source":"soc_travelers","target":"soc_travel_d","weight":0.65,"polarity":1,"label":"demand signal","label_ar":"إشارة الطلب"},
    {"id":"e99","source":"soc_expats","target":"soc_business","weight":0.75,"polarity":1,"label":"workforce","label_ar":"القوى العاملة"},
    {"id":"e100","source":"soc_expats","target":"eco_gdp","weight":0.55,"polarity":1,"label":"labor contribution","label_ar":"مساهمة العمالة"},
    {"id":"e101","source":"soc_expats","target":"soc_housing","weight":0.6,"polarity":1,"label":"housing demand","label_ar":"الطلب على السكن"},
    {"id":"e102","source":"eco_gdp","target":"soc_employment","weight":0.65,"polarity":1,"label":"job creation","label_ar":"خلق الوظائف"},
    {"id":"e103","source":"soc_employment","target":"soc_citizens","weight":0.6,"polarity":1,"label":"citizen welfare","label_ar":"رفاهية المواطنين"},
    {"id":"e104","source":"soc_employment","target":"soc_expats","weight":0.55,"polarity":1,"label":"expat demand","label_ar":"الطلب على العمالة"},
    {"id":"e43","source":"fin_insurers","target":"eco_shipping","weight":0.4,"polarity":-1,"label":"coverage constraint","label_ar":"قيود التغطية"},
    {"id":"e44","source":"fin_reinsure","target":"fin_ins_risk","weight":0.35,"polarity":-1,"label":"risk transfer","label_ar":"نقل المخاطر"},
    {"id":"e45","source":"soc_media","target":"fin_ins_risk","weight":0.3,"polarity":1,"label":"risk perception","label_ar":"إدراك المخاطر"},
    {"id":"e49","source":"soc_travel_d","target":"eco_tourism","weight":0.85,"polarity":1,"label":"tourism demand","label_ar":"طلب السياحة"},
    {"id":"e105","source":"soc_hajj","target":"eco_tourism","weight":0.8,"polarity":1,"label":"pilgrimage revenue","label_ar":"إيرادات الحج"},
    {"id":"e106","source":"soc_hajj","target":"inf_jed","weight":0.85,"polarity":1,"label":"pilgrim flow","label_ar":"تدفق الحجاج"},
    {"id":"e107","source":"soc_hajj","target":"soc_travelers","weight":0.7,"polarity":1,"label":"travel demand","label_ar":"الطلب على السفر"},
    {"id":"e108","source":"geo_sa","target":"soc_hajj","weight":0.9,"polarity":1,"label":"hosts","label_ar":"يستضيف"},
    {"id":"e109","source":"gov_tourism","target":"eco_tourism","weight":0.7,"polarity":1,"label":"tourism policy","label_ar":"سياسة السياحة"},
    {"id":"e110","source":"gov_tourism","target":"soc_hajj","weight":0.65,"polarity":1,"label":"pilgrim policy","label_ar":"سياسة الحج"},
    {"id":"e51","source":"eco_aramco","target":"fin_tadawul","weight":0.75,"polarity":1,"label":"market cap","label_ar":"القيمة السوقية"},
    {"id":"e52","source":"fin_tadawul","target":"fin_sama","weight":0.45,"polarity":1,"label":"market signal","label_ar":"إشارة السوق"},
    {"id":"e53","source":"eco_gdp","target":"fin_tadawul","weight":0.6,"polarity":1,"label":"economic health","label_ar":"الصحة الاقتصادية"},
    {"id":"e111","source":"gov_finance","target":"fin_sama","weight":0.75,"polarity":1,"label":"fiscal policy","label_ar":"السياسة المالية"},
    {"id":"e112","source":"gov_finance","target":"fin_tadawul","weight":0.6,"polarity":1,"label":"market oversight","label_ar":"الرقابة على السوق"},
    {"id":"e113","source":"gov_finance","target":"fin_banking","weight":0.65,"polarity":1,"label":"fiscal regulation","label_ar":"التنظيم المالي"},
    {"id":"e56","source":"geo_om","target":"eco_shipping","weight":0.55,"polarity":1,"label":"Strait access","label_ar":"الوصول للمضيق"},
    {"id":"e57","source":"geo_om","target":"geo_hormuz","weight":0.7,"polarity":1,"label":"controls strait","label_ar":"يتحكم بالمضيق"},
    {"id":"e58","source":"geo_bh","target":"fin_insurers","weight":0.45,"polarity":1,"label":"insurance hub","label_ar":"مركز تأمين"},
    {"id":"e59","source":"geo_bh","target":"eco_oil","weight":0.4,"polarity":1,"label":"oil production","label_ar":"إنتاج النفط"},
    {"id":"e60","source":"eco_oil","target":"inf_power","weight":0.7,"polarity":1,"label":"fuel for power","label_ar":"وقود للطاقة"},
    {"id":"e61","source":"inf_power","target":"inf_desal","weight":0.85,"polarity":1,"label":"powers desalination","label_ar":"يغذي التحلية"},
    {"id":"e62","source":"inf_desal","target":"soc_citizens","weight":0.75,"polarity":1,"label":"water supply","label_ar":"إمدادات المياه"},
    {"id":"e63","source":"inf_power","target":"soc_citizens","weight":0.7,"polarity":1,"label":"electricity supply","label_ar":"إمدادات الكهرباء"},
    {"id":"e64","source":"inf_power","target":"soc_business","weight":0.65,"polarity":1,"label":"business power","label_ar":"طاقة الأعمال"},
    {"id":"e65","source":"geo_sa","target":"inf_power","weight":0.8,"polarity":1,"label":"national grid","label_ar":"الشبكة الوطنية"},
    {"id":"e66","source":"geo_uae","target":"inf_desal","weight":0.75,"polarity":1,"label":"water infrastructure","label_ar":"البنية التحتية للمياه"},
    {"id":"e114","source":"inf_power","target":"inf_telecom","weight":0.7,"polarity":1,"label":"powers telecom","label_ar":"يغذي الاتصالات"},
    {"id":"e115","source":"inf_telecom","target":"eco_telecom","weight":0.8,"polarity":1,"label":"service delivery","label_ar":"تقديم الخدمات"},
    {"id":"e116","source":"eco_telecom","target":"soc_business","weight":0.6,"polarity":1,"label":"digital services","label_ar":"الخدمات الرقمية"},
    {"id":"e117","source":"eco_telecom","target":"soc_social","weight":0.55,"polarity":1,"label":"platform infra","label_ar":"بنية المنصات"},
    {"id":"e118","source":"gov_water","target":"inf_desal","weight":0.8,"polarity":1,"label":"oversees","label_ar":"يشرف على"},
    {"id":"e119","source":"gov_water","target":"inf_power","weight":0.75,"polarity":1,"label":"oversees","label_ar":"يشرف على"},
    {"id":"e120","source":"gov_transport","target":"eco_shipping","weight":0.7,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e121","source":"gov_transport","target":"eco_aviation","weight":0.7,"polarity":1,"label":"regulates","label_ar":"ينظّم"},
    {"id":"e122","source":"eco_shipping","target":"eco_food","weight":0.85,"polarity":1,"label":"food imports","label_ar":"واردات الغذاء"},
    {"id":"e123","source":"inf_jebel","target":"eco_food","weight":0.7,"polarity":1,"label":"port intake","label_ar":"استقبال الموانئ"},
    {"id":"e124","source":"inf_dammam","target":"eco_food","weight":0.6,"polarity":1,"label":"port intake","label_ar":"استقبال الموانئ"},
    {"id":"e125","source":"geo_hormuz","target":"eco_food","weight":0.65,"polarity":1,"label":"supply route","label_ar":"طريق الإمداد"},
    {"id":"e126","source":"eco_food","target":"soc_citizens","weight":0.8,"polarity":1,"label":"food supply","label_ar":"الإمداد الغذائي"},
    {"id":"e127","source":"eco_food","target":"soc_food_d","weight":0.75,"polarity":1,"label":"food availability","label_ar":"توفر الغذاء"},
    {"id":"e128","source":"soc_food_d","target":"soc_citizens","weight":0.7,"polarity":-1,"label":"food stress","label_ar":"ضغط غذائي"},
    {"id":"e129","source":"eco_food","target":"soc_expats","weight":0.65,"polarity":1,"label":"worker food supply","label_ar":"إمداد غذاء العمالة"},
    {"id":"e130","source":"gov_energy","target":"eco_oil","weight":0.85,"polarity":1,"label":"energy policy","label_ar":"سياسة الطاقة"},
    {"id":"e131","source":"gov_energy","target":"eco_aramco","weight":0.8,"polarity":1,"label":"oversees","label_ar":"يشرف على"},
    {"id":"e132","source":"gov_energy","target":"eco_fuel","weight":0.7,"polarity":1,"label":"fuel policy","label_ar":"سياسة الوقود"},
    {"id":"e133","source":"gov_energy","target":"inf_power","weight":0.65,"polarity":1,"label":"energy supply","label_ar":"إمداد الطاقة"},
    {"id":"e134","source":"eco_fuel","target":"soc_housing","weight":0.55,"polarity":1,"label":"cost driver","label_ar":"محرك التكاليف"},
    {"id":"e135","source":"soc_housing","target":"soc_citizens","weight":0.6,"polarity":1,"label":"living costs","label_ar":"تكاليف المعيشة"},
    {"id":"e148","source":"soc_media","target":"soc_sentiment","weight":0.7,"polarity":1,"label":"shapes sentiment","label_ar":"يشكّل المشاعر"},
    {"id":"e149","source":"soc_social","target":"soc_sentiment","weight":0.65,"polarity":1,"label":"amplifies","label_ar":"يضخّم"},
    {"id":"e138","source":"soc_sentiment","target":"soc_stability","weight":0.75,"polarity":1,"label":"affects stability","label_ar":"يؤثر على الاستقرار"},
    {"id":"e139","source":"soc_stability","target":"fin_tadawul","weight":0.5,"polarity":1,"label":"market confidence","label_ar":"ثقة السوق"},
    {"id":"e140","source":"eco_gdp","target":"soc_stability","weight":0.55,"polarity":1,"label":"prosperity signal","label_ar":"إشارة الرخاء"},
    {"id":"e141","source":"eco_food","target":"soc_stability","weight":0.65,"polarity":1,"label":"food stability","label_ar":"استقرار غذائي"},
    {"id":"e142","source":"inf_jebel","target":"eco_logistics","weight":0.85,"polarity":1,"label":"logistics hub","label_ar":"مركز لوجستي"},
    {"id":"e143","source":"eco_logistics","target":"eco_gdp","weight":0.5,"polarity":1,"label":"GDP contribution","label_ar":"مساهمة الناتج المحلي"},
    {"id":"e144","source":"eco_logistics","target":"eco_food","weight":0.6,"polarity":1,"label":"food distribution","label_ar":"توزيع الغذاء"},
    {"id":"e145","source":"inf_dmm","target":"eco_logistics","weight":0.45,"polarity":1,"label":"cargo hub","label_ar":"مركز شحن"},
    {"id":"e146","source":"eco_shipping","target":"fin_insurers","weight":0.8,"polarity":1,"label":"shipping risk drives premiums","label_ar":"مخاطر الشحن ترفع الأقساط"},
    {"id":"e147","source":"fin_insurers","target":"eco_aviation","weight":0.75,"polarity":1,"label":"insurance raises fuel cost","label_ar":"التأمين يرفع تكلفة الوقود"},
    {"id":"e150","source":"soc_ticket","target":"soc_travel_d","weight":0.8,"polarity":-1,"label":"price suppresses demand","label_ar":"السعر يخفض الطلب"},
    {"id":"e151","source":"soc_travel_d","target":"inf_airport_throughput","weight":0.85,"polarity":1,"label":"demand drives throughput","label_ar":"الطلب يحرك حركة المطارات"},
    {"id":"e152","source":"inf_airport_throughput","target":"eco_tourism","weight":0.8,"polarity":1,"label":"throughput drives tourism","label_ar":"حركة المطارات تدعم السياحة"},
    {"id":"e153","source":"inf_airport_throughput","target":"inf_ruh","weight":0.85,"polarity":1,"label":"throughput → RUH","label_ar":"الحركة → الرياض"},
    {"id":"e154","source":"inf_airport_throughput","target":"inf_dxb","weight":0.9,"polarity":1,"label":"throughput → DXB","label_ar":"الحركة → دبي"},
    {"id":"e155","source":"inf_airport_throughput","target":"inf_doh","weight":0.8,"polarity":1,"label":"throughput → DOH","label_ar":"الحركة → الدوحة"},
    {"id":"e156","source":"inf_airport_throughput","target":"inf_jed","weight":0.8,"polarity":1,"label":"throughput → JED","label_ar":"الحركة → جدة"},
    {"id":"e157","source":"inf_airport_throughput","target":"inf_kwi","weight":0.7,"polarity":1,"label":"throughput → KWI","label_ar":"الحركة → الكويت"},
    {"id":"e158","source":"inf_airport_throughput","target":"inf_auh","weight":0.75,"polarity":1,"label":"throughput → AUH","label_ar":"الحركة → أبوظبي"},
    {"id":"e159","source":"inf_airport_throughput","target":"inf_bah","weight":0.6,"polarity":1,"label":"throughput → BAH","label_ar":"الحركة → البحرين"},
    {"id":"e160","source":"inf_airport_throughput","target":"inf_mct","weight":0.55,"polarity":1,"label":"throughput → MCT","label_ar":"الحركة → مسقط"},
    {"id":"e161","source":"inf_airport_throughput","target":"inf_dmm","weight":0.65,"polarity":1,"label":"throughput → DMM","label_ar":"الحركة → الدمام"},
    {"id":"e162","source":"eco_aviation","target":"eco_saudia","weight":0.8,"polarity":1,"label":"fuel cost → Saudia","label_ar":"تكلفة الوقود → السعودية"},
    {"id":"e163","source":"eco_aviation","target":"eco_emirates","weight":0.85,"polarity":1,"label":"fuel cost → Emirates","label_ar":"تكلفة الوقود → الإمارات"},
    {"id":"e164","source":"eco_aviation","target":"eco_qatar_aw","weight":0.8,"polarity":1,"label":"fuel cost → Qatar","label_ar":"تكلفة الوقود → القطرية"},
    {"id":"e165","source":"eco_saudia","target":"eco_gdp","weight":0.45,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e166","source":"eco_emirates","target":"eco_gdp","weight":0.5,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e167","source":"eco_qatar_aw","target":"eco_gdp","weight":0.4,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e168","source":"inf_airport_throughput","target":"eco_saudia","weight":0.7,"polarity":1,"label":"passengers → Saudia","label_ar":"المسافرون → السعودية"},
    {"id":"e169","source":"inf_airport_throughput","target":"eco_emirates","weight":0.8,"polarity":1,"label":"passengers → Emirates","label_ar":"المسافرون → الإمارات"},
    {"id":"e170","source":"inf_airport_throughput","target":"eco_qatar_aw","weight":0.7,"polarity":1,"label":"passengers → Qatar","label_ar":"المسافرون → القطرية"},
    {"id":"e171","source":"eco_saudia","target":"inf_ruh","weight":0.8,"polarity":1,"label":"Saudia hub → RUH","label_ar":"مركز السعودية → الرياض"},
    {"id":"e172","source":"eco_emirates","target":"inf_dxb","weight":0.9,"polarity":1,"label":"Emirates hub → DXB","label_ar":"مركز الإمارات → دبي"},
    {"id":"e173","source":"eco_qatar_aw","target":"inf_doh","weight":0.85,"polarity":1,"label":"Qatar hub → DOH","label_ar":"مركز القطرية → الدوحة"},
    {"id":"e174","source":"eco_saudia","target":"inf_jed","weight":0.75,"polarity":1,"label":"Saudia → JED","label_ar":"السعودية → جدة"},
    {"id":"e175","source":"eco_aviation","target":"eco_kw_airways","weight":0.7,"polarity":1,"label":"fuel cost → Kuwait Airways","label_ar":"تكلفة الوقود → الكويتية"},
    {"id":"e176","source":"eco_aviation","target":"eco_gulf_air","weight":0.65,"polarity":1,"label":"fuel cost → Gulf Air","label_ar":"تكلفة الوقود → طيران الخليج"},
    {"id":"e177","source":"eco_aviation","target":"eco_oman_air","weight":0.6,"polarity":1,"label":"fuel cost → Oman Air","label_ar":"تكلفة الوقود → الطيران العماني"},
    {"id":"e178","source":"eco_kw_airways","target":"inf_kwi","weight":0.8,"polarity":1,"label":"Kuwait Airways hub → KWI","label_ar":"الكويتية → الكويت"},
    {"id":"e179","source":"eco_gulf_air","target":"inf_bah","weight":0.8,"polarity":1,"label":"Gulf Air hub → BAH","label_ar":"طيران الخليج → البحرين"},
    {"id":"e180","source":"eco_oman_air","target":"inf_mct","weight":0.8,"polarity":1,"label":"Oman Air hub → MCT","label_ar":"الطيران العماني → مسقط"},
    {"id":"e181","source":"inf_airport_throughput","target":"eco_kw_airways","weight":0.6,"polarity":1,"label":"passengers → Kuwait Airways","label_ar":"المسافرون → الكويتية"},
    {"id":"e182","source":"inf_airport_throughput","target":"eco_gulf_air","weight":0.55,"polarity":1,"label":"passengers → Gulf Air","label_ar":"المسافرون → طيران الخليج"},
    {"id":"e183","source":"inf_airport_throughput","target":"eco_oman_air","weight":0.5,"polarity":1,"label":"passengers → Oman Air","label_ar":"المسافرون → الطيران العماني"},
    {"id":"e184","source":"eco_kw_airways","target":"eco_gdp","weight":0.3,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e185","source":"eco_gulf_air","target":"eco_gdp","weight":0.25,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e186","source":"eco_oman_air","target":"eco_gdp","weight":0.25,"polarity":-1,"label":"airline cost drags GDP","label_ar":"تكلفة الطيران تضغط الناتج"},
    {"id":"e187","source":"eco_aviation","target":"eco_av_stress","weight":0.85,"polarity":1,"label":"fuel cost → stress","label_ar":"تكلفة الوقود → الضغط"},
    {"id":"e188","source":"fin_insurers","target":"eco_av_stress","weight":0.7,"polarity":1,"label":"insurance → stress","label_ar":"التأمين → الضغط"},
    {"id":"e189","source":"soc_ticket","target":"eco_av_stress","weight":0.65,"polarity":1,"label":"flight cost → stress","label_ar":"تكلفة الرحلات → الضغط"},
    {"id":"e190","source":"inf_airport_throughput","target":"eco_av_stress","weight":0.6,"polarity":-1,"label":"throughput drop → stress","label_ar":"انخفاض الحركة → الضغط"},
    {"id":"e191","source":"eco_av_stress","target":"eco_gdp","weight":0.5,"polarity":-1,"label":"aviation stress drags GDP","label_ar":"ضغط الطيران يضغط الناتج"},
]


_node_index: dict[str, dict] = {}
_edge_index: dict[str, dict] = {}
_adjacency: dict[str, list[dict]] = {}


def _ensure_indexes():
    if not _node_index:
        for n in NODES:
            _node_index[n["id"]] = n
    if not _edge_index:
        for e in EDGES:
            _edge_index[e["id"]] = e
    if not _adjacency:
        for e in EDGES:
            _adjacency.setdefault(e["source"], []).append(e)


def get_node(node_id: str) -> Optional[dict]:
    _ensure_indexes()
    return _node_index.get(node_id)


def get_nodes_by_layer(layer: str) -> list[dict]:
    return [n for n in NODES if n["layer"] == layer]


def get_edge(edge_id: str) -> Optional[dict]:
    _ensure_indexes()
    return _edge_index.get(edge_id)


def get_adjacency(node_id: str) -> list[dict]:
    _ensure_indexes()
    return _adjacency.get(node_id, [])


def get_all_nodes() -> list[dict]:
    """Return all 76 nodes."""
    return list(NODES)


def get_all_edges() -> list[dict]:
    """Return all edges."""
    return list(EDGES)


def get_all_layers() -> list[str]:
    return sorted(set(n["layer"] for n in NODES))


def get_node_count() -> int:
    return len(NODES)


def get_edge_count() -> int:
    return len(EDGES)
