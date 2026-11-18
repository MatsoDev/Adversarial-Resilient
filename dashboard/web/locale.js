'use strict';
// UI copy only. Never translate artifact JSON, hashes, model names or numeric evidence.
(() => {
  const copy = [
    ['ARSM · Threat context and transfer','ARSM · سياق التهديد ونقل الهجوم'],
    ['Threat context and transfer','سياق التهديد ونقل الهجوم'],
    ['White-box and black-box evidence','أدلة الهجوم بمعرفة الموديل ومن غيرها'],
    ['Recorded results only. No training, live attacks or uploads.','نتائج مسجّلة بس. مفيش تدريب ولا هجمات مباشرة ولا رفع ملفات.'],
    ['Four separate realism questions','أربع أسئلة منفصلة عن واقعية التعديل'],
    ['Scalar feature feasibility','صلاحية قيم الخصائص الفردية'],
    ['Policy projection checks numeric bounds, integer values and immutable coordinates only.','تطبيق القيود بيراجع الحدود الرقمية والأعداد الصحيحة والخصائص الثابتة بس.'],
    ['Coupled structural consistency','اتساق الخصائص المترابطة والبنية'],
    ['Not established. Derived features are not recomputed together.','مش مثبت. الخصائص المشتقة مش بيتعاد حسابها مع بعض.'],
    ['Executable realizability','إمكانية تطبيق التعديل على ملف تنفيذي'],
    ['Not established. No authorized isolated-lab PE demonstration.','مش مثبت. مفيش تجربة PE في معمل معزول بتصريح.'],
    ['Preserved behavior','الحفاظ على السلوك'],
    ['Not established. No executable was modified or run.','مش مثبت. مفيش ملف تنفيذي اتعدّل أو اتشغّل.'],
    ['Owner authorization is not technical Security review. A feature edit proves none of the other three properties.','تصريح المالك مش مراجعة تقنية من فريق الأمن. تعديل خاصية مش بيثبت أي خاصية من التلاتة التانيين.'],
    ['Proposed threat mappings','ربط مقترح بتصنيفات التهديد'],
    ['Technical Security review pending. Mappings describe methods and intent, not successful real-world compromise.','مراجعة فريق الأمن التقنية لسه مطلوبة. الربط بيوصف الطريقة والهدف، مش اختراق حقيقي ناجح.'],
    ['Scope and missing evidence','النطاق والأدلة الناقصة'],
    ['HopSkipJump and ZOO: not implemented, not run. CICIDS: inactive; no trained IDS evidence. Problem-space lab: not authorized, not run. M1 and frozen-benchmark acceptance remain separate.','HopSkipJump وZOO: متنفّذوش ومشتغلوش. CICIDS مش نشط؛ مفيش دليل على IDS مدرّب. معمل الملفات الفعلية: من غير تصريح ومتعملش. اعتماد M1 والتقييم المجمّد لسه منفصلين.'],
    ['Transfer ASR uses target-clean-correct rows, not source successes. Conditional transfer additionally requires both models initially correct and source attack success. Preexisting errors are never attack successes.','نسبة نجاح النقل بتتحسب من العينات اللي الهدف كان مصنّفها صح، مش نجاحات المصدر. النقل المشروط كمان بيشترط إن الموديلين كانوا صح والهجوم نجح على المصدر. الأخطاء القديمة مش نجاحات هجوم.'],
    ['Malware evasion counts initially detected malicious rows made benign. False-positive induction counts initially correct benign rows made malicious. Empty denominators are unavailable, not zero.','التفويت بيحسب العينات الضارة المكتشفة صح اللي اتصنّفت سليمة بعد التعديل. الإنذارات الكاذبة بتحسب السليمة الصح اللي اتصنّفت ضارة. المقام الفاضي غير متاح، مش صفر.'],
    ['Shared training data and preprocessing are attacker knowledge assumptions, not a strict unknown-data black-box scenario.','مشاركة داتا التدريب والتحويل الرقمي افتراض عن معرفة المهاجم، مش سيناريو بياناته مجهولة بالكامل.'],
    ['Pending / unavailable','منتظر / غير متاح'],
    ['White-box and black-box results','نتائج الهجوم بمعرفة الموديل ونقل الهجوم'],
    ['Attacker knowledge and provenance','معرفة المهاجم ومصدر الأدلة'],
    ['Source gradients only; no target feedback during crafting. Public true labels. All rows retained, with no target-based filtering.','تدرّجات المصدر بس؛ مفيش رد من الهدف أثناء التوليد. التصنيفات الحقيقية عامة. كل العينات موجودة من غير فلترة حسب الهدف.'],
    ['White-box target gradients. Transfer has not been measured in this snapshot.','الهجوم استخدم تدرّجات الهدف. نقل الهجوم متقاسش في التجربة دي.'],
    ['Correct / all rows; ASR numerator / clean-correct denominator. Class-specific rates use class-specific clean-correct denominators.','الصح / كل العينات؛ نسبة النجاح: الأخطاء الجديدة / القرارات الصحيحة أصلًا. كل فئة ليها مقام من قراراتها الصحيحة.'],
    ['Knowledge','المعرفة'],['Model','الموديل'],['Attacked correct','الصح بعد الهجوم'],
    ['Malware evasion','تفويت عينات ضارة'],['False-positive induction','توليد إنذارات كاذبة'],['Preexisting errors','أخطاء موجودة قبل الهجوم'],
    ['Surrogate white-box','معرفة كاملة بالموديل البديل'],['Black-box transfer','نقل هجوم من غير معرفة الهدف'],['White-box','معرفة كاملة بالموديل'],['Source','المصدر'],['Target','الهدف'],
    ['Conditional transfer','نقل مشروط'],['Transferred sample digest','بصمة العينات المنقولة'],
    ['Deliberately selected case studies are available in the AI journey when recorded.','الحالات المختارة عمدًا للشرح متاحة في الرحلة لما تكون مسجّلة.'],
    ['Transfer results pending. Recorded white-box results are not black-box evidence.','نتائج نقل الهجوم منتظرة. نتائج المعرفة الكاملة المسجّلة مش دليل على نقل الهجوم.'],
    ['No measured results available. Missing evidence is not a zero success rate.','مفيش نتائج مقاسة متاحة. الدليل الناقص مش نسبة نجاح صفر.'],
    ['Threat mappings unavailable.','ربط التهديدات مش متاح.'],
    ['OWASP ML07 transfer learning is not adversarial-example transfer. ATLAS evasion intent does not establish executable evasion.','التعلم المنقول في OWASP ML07 مش نقل أمثلة تضليلية. هدف التفويت في ATLAS مش إثبات تفويت بملف تنفيذي.'],
    ['Could not load results. Use refresh to retry.','تعذّر تحميل النتائج. استخدم التحديث علشان تحاول تاني.'],
    ['Completed snapshots: ','تجارب مكتملة: '],
    ['Feature-space only','خصائص رقمية بس'],
    ['Scalar constraints only. Coupled consistency, executable realizability and preserved behavior are not established.','قيود على خصائص فردية بس. الاتساق المترابط وإمكانية تنفيذ التعديل والحفاظ على السلوك مش مثبتين.'],
    ['Source and target decisions','قرارات المصدر والهدف'],
    ['Known label: ','التصنيف المعروف: '],
    ['. Scores are not file-safety guarantees.',' . الدرجات مش ضمان لأمان الملف.'],
    ['White-box target gradients. Transfer has not been measured for this case.','الهجوم استخدم تدرّجات الهدف. نقل الهجوم متقاسش للحالة دي.'],
    ['This is a research prototype, not an assurance that a file is safe.','ده نموذج بحثي، مش ضمان إن الملف آمن.'],
    ['Model readiness details','تفاصيل جاهزية الموديل'],
    ['How should I read the scores?','أفهم درجات الموديل إزاي؟'],
    ['Recorded file-size value','قيمة حجم الملف المسجّلة'],
    ['Benign means non-malicious. Malicious means labelled as malware. A model prediction is not a file-safety guarantee.','Benign يعني غير ضار، وMalicious يعني متصنّف برمجية ضارة. توقّع الموديل مش ضمان لأمان الملف.'],
    ['A SIMPLE GUIDE TO OUR RESEARCH','افهم فكرة المشروع ببساطة'],
    ['Can an AI security guard be fooled?','هل ممكن نخدع حارس أمن بالـAI؟'],
    ['We train AI to tell benign and malicious file features apart. Then we deliberately challenge its decisions to find weaknesses before relying on it.','بندرّب AI يفرّق بين خصائص الملفات السليمة والضارة. وبعدين بنحاول نخدع قراراته علشان نكتشف نقاط ضعفه قبل ما نعتمد عليه.'],
    ['How this project works','المشروع بيشتغل إزاي'],
    ['01 / TRAIN','01 / ندرّب'],['02 / CHALLENGE','02 / نختبر'],['03 / IMPROVE','03 / نقوّي'],
    ['Teach it the difference','نعلّمه يفرّق'],
    ['Learn from examples with known benign or malicious labels.','يتعلّم من أمثلة معروف مسبقًا إنها سليمة أو ضارة.'],
    ['Try to change its answer','نحاول نغيّر إجابته'],
    ['Change allowed input features and check whether a correct answer becomes wrong.','نعدّل خصائص مسموحة ونشوف هل إجابته الصح هتتحوّل لغلط.'],
    ['Measure, then strengthen','نقيس النتيجة وبعدين نقوّيه'],
    ['Count the failures. Later, add defenses and repeat the test to measure improvement.','نحسب الأخطاء. بعدين نضيف دفاعات ونعيد الاختبار علشان نقيس هل اتحسّن.'],
    ['Defense work is planned for Sprints 9–12.','الدفاعات مخططة في Sprint 9–12.'],
    ['Now see one real example.','تعالى نشوف مثال حقيقي.'],
    ['Three short steps. No AI knowledge needed. You are replaying a recorded experiment.','3 خطوات بسيطة، من غير خلفية عن الـAI. إنت بتشوف إعادة عرض لتجربة مسجّلة.'],
    ['Start the walkthrough ↓','ابدأ المثال ↓'],
    ['The questions behind the project','أسئلة تساعدك تفهم الفكرة'],
    ['What is EMBER, and what is a sample?','إيه EMBER وإيه العينة؟'],
    ["EMBER contains numeric descriptions extracted from Windows programs, with known labels where available. A sample here is one description, like a file's information card. We do not run the original program.",'EMBER فيها أوصاف رقمية مستخرجة من برامج ويندوز، ومعاها التصنيف المعروف لما يكون متاح. العينة هنا وصف واحد، زي بطاقة معلومات عن الملف. مش بنشغّل البرنامج الأصلي.'],
    ['Who would use this, and why?','مين ممكن يستخدم ده وليه؟'],
    ['Security researchers and teams building AI detectors can use these tests to find weaknesses and compare model versions before deployment. This research prototype is not a complete antivirus product.','باحثو الأمن والتيم اللي بيبني كاشف بالـAI يقدروا يكتشفوا نقاط الضعف ويقارنوا نسخ الموديل قبل التشغيل. المشروع نموذج بحثي، مش برنامج حماية متكامل.'],
    ['Did we actually change a malware file?','هل عدّلنا ملف ضار فعلي؟'],
    ['No. This experiment changes recorded feature values only. A decision change does not prove that a valid executable could be modified in the same way.','لأ. التجربة بتعدّل قيم خصائص مسجّلة بس. تغيّر القرار مش إثبات إننا نقدر نعدّل ملف تنفيذي صالح بنفس الطريقة.'],
    ['Does one fooled example prove the whole model is bad?','هل مثال اتخدع معناه الموديل كله وحش؟'],
    ['No. A case explains what happened once. The larger experiment measures how often it happened, under the exact model, sample selection and constraints shown.','لأ. الحالة بتشرح اللي حصل مرة. التجربة الأكبر بتقيس ده اتكرر قد إيه، بنفس الموديل واختيار العينات والقيود المعروضة.'],
    ['See the model score','شوف درجة الموديل'],
    ['Recorded example walkthrough','شرح مثال مسجّل'],
    ['A file description. One decision. One challenge.','وصف ملف، وقرار موديل، ومحاولة خداع.'],
    ['Walkthrough steps','خطوات المثال'],
    ['1 · Original sample','1 · العينة الأصلية'],['2 · The change','2 · التعديل'],['3 · The result','3 · النتيجة'],
    ['STEP 1 OF 3','الخطوة 1 من 3'],['STEP 2 OF 3','الخطوة 2 من 3'],['STEP 3 OF 3','الخطوة 3 من 3'],
    ['First, check the answer before any attack.','الأول، نشوف الإجابة قبل أي هجوم.'],
    ['The dataset tells us the known label. The AI makes its own prediction. Comparing the two tells us whether the AI started out correct.','الداتا بتقولنا التصنيف المعروف، والـAI بيعمل توقّعه. نقارن الاتنين علشان نعرف هل بدأ بإجابة صح.'],
    ['The AI got this example right. Next, we will challenge that decision.','الـAI جاوب صح في المثال ده. الخطوة الجاية نحاول نخدع القرار.'],
    ['The AI was already wrong here. Keep that in mind: this is not an attack-induced error.','الـAI كان غلطان من الأول هنا. خليك فاكر إن ده مش خطأ سبّبه الهجوم.'],
    ['Change the description, then ask the AI again.','نغيّر الوصف ونسأل الـAI تاني.'],
    ['An adversarial attack deliberately looks for an allowed change that makes the model answer incorrectly. We replay the measured change below; no experiment runs in your browser.','الهجوم التضليلي بيدوّر على تعديل مسموح يخلي الموديل يجاوب غلط. تحت بنعرض التعديل اللي اتقاس فعلًا؛ مش بنشغّل تجربة من المتصفح.'],
    ['What this means in this experiment','ده معناه إيه في التجربة دي'],
    ['Only the listed numeric features changed. For this size-only probe, all other 2,380 coordinates stayed fixed. The raw size values above are approximate bytes, reconstructed from the measured model inputs.','الخصائص الرقمية المعروضة بس هي اللي اتغيّرت. في تجربة الحجم دي، باقي الـ2,380 خاصية فضلت ثابتة. قيم الحجم الخام فوق تقريبية بالبايت، محسوبة عكسيًا من مدخلات الموديل المقاسة.'],
    ['Only the listed numeric features changed above the measurement tolerance. Raw values are approximate inverse transforms of the measured model inputs.','الخصائص المعروضة بس اتغيّرت فوق حد القياس. القيم الخام تقريبية، محسوبة عكسيًا من مدخلات الموديل المقاسة.'],
    ['This recorded attempt produced no feature change above the measurement tolerance. That is a real outcome too.','المحاولة المسجّلة دي مغيرتش خصائص فوق حد القياس. ودي برضه نتيجة حقيقية.'],
    ['No bytes in an actual file were changed. We are testing the model on feature descriptions.','مغيرناش بايتات في ملف فعلي. إحنا بنختبر الموديل على أوصاف الخصائص.'],
    ['Technical attack settings','إعدادات الهجوم التقنية'],
    ['Why does this matter?','ده مهم ليه؟'],
    ['This test helps engineers find where an AI detector can fail. They can then compare a stronger version under the same conditions. One case explains a failure; the whole cohort measures its frequency.','الاختبار بيساعد المهندسين يعرفوا كاشف الـAI ممكن يغلط فين. بعدها يقارنوا نسخة أقوى بنفس الظروف. الحالة بتشرح مثال، ومجموعة العينات بتقيس ده بيحصل قد إيه.'],
    ['How often did this happen in the experiment?','ده حصل كام مرة في التجربة؟'],
    ['Previous step','الخطوة اللي فاتت'],['Next: see the change →','التالي: شوف التعديل ←'],['Next: see the result →','التالي: شوف النتيجة ←'],['Restart walkthrough ↻','ابدأ المثال من الأول ↻'],
    ['Problem-space validity: not established.','صلاحية التعديل على ملف فعلي: غير مثبتة.'],
    ['ARSM · AI deception journey','ARSM · رحلة خداع الذكاء الاصطناعي'],
    ['Main navigation','التنقل الرئيسي'],['Malicious-class score','درجة الفئة الضارة'],
    ['AI resilience lab','معمل اختبار الـAI'],
    ['AI deception journey','رحلة خداع الـAI'],
    ['Attack comparison','مقارنة الهجمات'],
    ['Models and data','الموديلات والبيانات'],
    ['Recorded research experiments','تجارب بحثية مسجّلة'],
    ['Same release = same team starting point','نفس الإصدار = نفس نقطة بداية التيم'],
    ['ARSM / Understand the experiment','ARSM / تجربة تقدر تفهمها'],
    ['UNDERSTAND IT, STEP BY STEP','افهم التجربة، خطوة بخطوة'],
    ['Can we fool an AI decision?','هل ممكن نخدع قرار الـAI؟'],
    ['Follow an EMBER sample: the original decision, a constrained feature change, and the result.','نشوف عينة من EMBER، قرار الموديل قبل الهجوم، وإيه حصل بعد تعديل خصائص محددة.'],
    ['We test ','بنختبر '],
    ['features extracted from files','خصائص مستخرجة من ملفات'],
    [', without executing them. This is not an antivirus scan or proof of a valid file modification.','، من غير تشغيلها. ده مش فحص فيروسات، ولا إثبات إن التعديل ينفع يتطبّق على ملف حقيقي.'],
    ['Choose a different experiment, attack or case','اختار تجربة، هجوم أو حالة تانية'],
    ['The first recorded successful attempt is selected when available. No attacks or training run from this page.','المعروض تلقائيًا أول محاولة ناجحة مسجّلة، لو موجودة. مفيش هجمات أو تدريب بيشتغلوا من الصفحة.'],
    ['Experiment','التجربة'],['Attack and parameters','الهجوم وإعداداته'],['Selected case','الحالة المعروضة'],
    ['Loading measured results…','بنحمّل النتائج الحقيقية…'],
    ['What are we trying to establish?','إحنا بنحاول نثبت إيه؟'],
    ['High accuracy alone is not enough. We test whether an attack changes correct decisions, then measure whether defenses help without damaging normal performance.','الدقة العالية لوحدها مش كفاية. بنختبر هل الموديل يتلخبط تحت محاولة خداع، وبعدين نقيس هل الدفاعات بتقلّل المشكلة من غير ما تبوّظ قراراته العادية.'],
    ['Open the numbers and research details →','افتح كل الأرقام والتفاصيل البحثية ←'],
    ['Successful attack','محاولة خداع نجحت'],['Remained correct','الموديل فضل صح'],['Preexisting error','خطأ موجود قبل الهجوم'],
    ['The model was already wrong. This case is not evidence of a successful attack and is excluded from the ASR denominator.','الموديل كان غلطان من البداية. الحالة دي مش دليل إن الهجوم خدعه، ومش بتدخل في مقام نسبة نجاح الهجوم.'],
    ['The model stayed correct after this attempt. That is one resisted case, not a guarantee against every attack.','الموديل فضل مصنّف العينة صح بعد المحاولة دي. ده نجاح في الحالة دي بس، مش ضمان إنه يقاوم كل الهجمات.'],
    ['The model initially detected this malicious sample, then called it benign after the feature change. This attempt successfully fooled the decision on this feature row.','الموديل اكتشف العينة الضارة صح في الأول، وبعد التعديل صنّفها سليمة بالغلط. محاولة الخداع نجحت على خصائص العينة دي.'],
    ['This sample is benign. The model was initially correct, but the change caused a malicious verdict: a false alarm, not malware escaping detection.','العينة سليمة والموديل كان مصنّفها صح، وبعد التعديل صنّفها ضارة بالغلط. الهجوم سبّب إنذار كاذب؛ دي مش حالة ملف ضار عدّى من الكشف.'],
    ['Experimental detector — research only','موديل تجريبي — لسه مش معتمد'],
    ['Frozen evaluation model','موديل مجمّد للتقييم'],
    ['Full operating-validation accuracy: ','دقته على التحقق الكامل '],
    [', below the 93% freeze gate. Small-cohort results below do not replace full validation.','، وشرط الاعتماد 93%. أرقام المجموعة الصغيرة تحت مش بديل للتقييم الكامل.'],
    ['A frozen model does not establish that a feature edit is a valid executable modification.','اعتماد الموديل مش معناه إن كل تعديل في الخصائص صالح كملف فعلي.'],
    [' Constraint review: ',' مراجعة قيود التجربة: '],
    ['ONE MEASURED CASE','حالة فردية من تجربة فعلية'],
    ['Know the ground truth','نعرف الحقيقة'],['Read the original decision','نشوف قرار الموديل'],['Compare after the attack','نقارن بعد الهجوم'],
    ['Known dataset label: ','التصنيف المعروف في الداتا: '],
    ['This reference label is how we judge correctness; it is not a model guess.','ده المرجع اللي بنقيس عليه صحة القرار، مش تخمين من الموديل.'],
    ['Before attack','قبل الهجوم'],['After attack','بعد الهجوم'],
    ['Malicious','ضارة'],['Benign','سليمة'],
    ['Correct decision','قرار صحيح'],['Incorrect decision','قرار غلط'],
    [' against the known label',' مقارنة بالتصنيف المعروف'],
    ['Model score for malicious: ','درجة الموديل للفئة الضارة: '],
    ['The score is not file safety or attack success rate. The classification threshold is 50%.','الدرجة مش نسبة أمان الملف، ومش نسبة نجاح الهجوم. حد التصنيف هنا 50%.'],
    ['What happened?','يعني إيه اللي حصل؟'],['What changed?','إيه اللي اتغيّر؟'],
    ['File size · general.size','حجم الملف · general.size'],
    ['Feature','الخاصية'],['Before','قبل'],['After ≈','بعد ≈'],
    ['No coordinates changed above the 10⁻⁶ measurement tolerance.','مفيش خصائص اتغيّرت فوق حد القياس 10⁻⁶.'],
    ['Raw values after the change are approximate inverse transforms, rounded for integer features. These are feature edits, not edits to an actual file.','القيم الخام بعد التعديل تقريبية: معكوس التحويل الرقمي، مع تقريب الخصائص الصحيحة. ده تعديل في الخصائص، مش تعديل ملف فعلي.'],
    ['Perturbation size and attack parameters','مقدار التعديل وإعدادات الهجوم'],
    ['Norms use standardized model coordinates; ε is not a percentage.','المقادير على إحداثيات الموديل المعيارية؛ ε مش نسبة مئوية.'],
    ['Planned · Sprint 9–12','مخطط · Sprint 9–12'],
    ['What happens after hardening?','وبعد ما نقوّي الموديل؟'],
    ['We will add measured hardened-model comparisons and re-attack that model. Defense results are not available yet; no improvement is assumed.','هنضيف مقارنة مع موديل مدرّب على مقاومة الهجمات، ونعيد الهجوم عليه. مفيش نتائج دفاعات لسه، فمش هنعرض تحسّن افتراضي.'],
    ['One case in a bigger picture','الحالة دي جزء من صورة أكبر'],
    ['The first available case of each outcome is deliberately selected for explanation, not as an independent statistical sample.','بنختار أول حالة متاحة لكل نوع نتيجة للشرح. الاختيار مقصود، مش عينة إحصائية مستقلة.'],
    ['evaluated samples','عينة في التجربة'],['correct decisions: before → after','قرارات صح قبل ← بعد'],
    ['induced errors / initially correct · ','اتخدعت من اللي كانت صح · '],
    ['ASR includes errors induced in either class, not only missed malicious samples.','نسبة النجاح بتشمل تحويل القرار للغلط في الفئتين، مش بس تفويت عينات ضارة.'],
    ['Case provenance and comparison limits','مصدر الحالة وحدود المقارنة'],
    ['Same recorded model, cohort and policy. The row is a dataset split reference, not an uploaded filename. No executables or complete feature arrays reach the browser.','نفس الموديل والمجموعة والقيود المحددة في التجربة. الصف هو مرجع داخل split الداتا، مش اسم ملف مرفوع. لا ملفات تنفيذية ولا مصفوفات خصائص كاملة بتوصل للمتصفح.'],
    ['Larger evaluations and an accepted baseline are needed before generalizing. Aggregate-only historical reports remain available in Attack comparison.','لازم نختبر مجموعات أكبر وموديل معتمد قبل أي تعميم. الحالات القديمة اللي مفيهاش تفاصيل فردية بتفضل متاحة في مقارنة الهجمات.'],
    ['No individual case is recorded for this configuration. Open Attack comparison for aggregate results.','مفيش حالة فردية مسجّلة للإعدادات دي. الإحصائيات العامة موجودة في مقارنة الهجمات.'],
    ['No measured individual cases are available yet. Open Attack comparison for aggregate results; we will not invent a story from aggregate numbers.','لسه مفيش حالات فردية مقاسة متاحة. افتح مقارنة الهجمات للنتائج العامة؛ مش هنولّد قصة من أرقام مجمّعة.'],
    ['experiment(s) with measured individual cases.','تجربة فيها حالات فردية مسجّلة.'],
    ['Invalid reports excluded: ','تم استبعاد '],[' invalid reports.','تقارير غير صالحة.'],
    [' The list is bounded; not all reports are shown.',' القائمة محدودة؛ مش كل التقارير معروضة.'],
    ['Could not load results. Check that the API is running, then ','تعذّر تحميل النتائج. اتأكد إن الـAPI شغّال، وبعدها '],['Retry','جرّب تاني'],
    // Shared navigation and the existing research views. Technical names stay English.
    ['← AI journey','← رحلة خداع الـAI'],['AI journey','رحلة خداع الـAI'],['Models & data','الموديلات والبيانات'],
    ['Attack results','نتائج الهجمات'],['Overview','نظرة عامة'],['Model performance','أداء الموديلات'],
    ['Dataset explorer','استكشاف البيانات'],['Methodology','المنهجية'],['Tooling demo','تجربة الأدوات'],
    ['WORKSPACE','مساحة العمل'],['Workspace','مساحة العمل'],['RESEARCH ENVIRONMENT','بيئة بحثية'],
    ['Build. Challenge. Defend.','ابني. اختبر. قوّي.'],['↻ Refresh results','↻ تحديث النتائج'],['↻ Refresh data','↻ تحديث البيانات'],
    ['How does the baseline hold up?','الموديل بيقاوم الهجمات قد إيه؟'],
    ['Measured clean and attacked results, with the conditions behind every number.','نتائج مقاسة قبل الهجوم وبعده، ومعاها ظروف كل رقم.'],
    ['Loading completed experiments…','بنحمّل التجارب المكتملة…'],['Experiment snapshot','نسخة التجربة'],
    ['All compatible attacks','كل الهجمات المتوافقة'],['Norm','مقياس التعديل'],['Attack','الهجوم'],
    ['One exact model, dataset, split, row subset and policy per snapshot. Norms stay separate.','كل تجربة ليها موديل وداتا وتقسيم ومجموعة عينات وقيود محددة. مقاييس التعديل بتفضل منفصلة.'],
    ['Comparison identity','هوية المقارنة'],['Model, cohort and policy provenance','مصدر الموديل والعينات والقيود'],
    ['CLEAN ACCURACY','الدقة قبل الهجوم'],['EVALUATED ROWS','العينات المختبرة'],['ASR DENOMINATOR','مقام نسبة نجاح الهجوم'],['MAXIMUM MEASURED ASR','أكبر نسبة نجاح مقاسة'],
    ['Identical rows for every displayed result','نفس العينات لكل النتائج المعروضة'],['Originally correct · both classes','القرارات الصحيحة أصلًا · الفئتين'],
    ['Accuracy versus epsilon','الدقة مقابل قوة التعديل ε'],['Clean versus attacked · measured results','قبل الهجوم وبعده · نتائج مقاسة'],
    ['Read the numbers','افهم الأرقام'],['Back to dashboard','ارجع للواجهة'],
    ['Resilience starts with visibility.','افهم النتائج علشان تختبر القوة.'],
    ['A clear view of your data, baseline models and measured results.','نظرة واضحة على الداتا والموديلات والنتائج المقاسة.'],
    ['Every model. Every metric.','الموديلات ونتائجها.'],['Compare measured performance on the same validation data.','قارن الأداء على نفس بيانات التحقق.'],
    ['Know the data behind the decision.','اعرف الداتا اللي ورا القرار.'],['Explore dataset composition, quality and reproducible provenance.','شوف تركيب الداتا وجودتها ومصدرها.'],
    ['Built on evidence.','مبني على نتائج موثّقة.'],['Understand the threat model, feature constraints and research limitations.','افهم نموذج التهديد وقيود الخصائص وحدود البحث.'],
    ['A separate proving ground.','تجربة منفصلة لتجهيز الأدوات.'],['MNIST demonstrates the attack tooling; it is separate from malware results.','MNIST بتختبر أدوات الهجوم؛ نتائجها منفصلة عن نتائج الملفات الضارة.'],
    ['Research API online','الـAPI شغّال'],['Connecting','جاري الاتصال'],['API unavailable','الـAPI مش متاح'],
    ['Loading research results…','بنحمّل نتائج البحث…'],['Unavailable','غير متاح'],
    ['Dataset','مجموعة البيانات'],['Inspect model','اختار الموديل'],['Document','المستند'],
    ['Known limitations','القيود المعروفة'],['Research notes','ملاحظات البحث'],
    ['CLASS','الفئة'],['RECORDS','عدد السجلات'],['MODEL','الموديل'],['ACCURACY','الدقة'],['PRECISION','دقة التنبؤات الضارة'],['RECALL','اكتشاف العينات الضارة'],
    ['Source class composition','توزيع الفئات'],['Recorded data splits','تقسيمات الداتا المسجّلة'],['Provenance and limitations','المصدر والقيود'],
    ['Interpret this result','افهم النتيجة'],['Where the model gets it right — and wrong','إمتى الموديل صح وإمتى بيغلط'],
    ['Reproducibility & training history','إعادة التجربة وسجل التدريب'],['Full stored experiment and reproducibility data','التجربة المسجّلة وبيانات إعادة تنفيذها'],
    ['ATTACK / PARAMETERS','الهجوم / الإعدادات'],['CLEAN','قبل الهجوم'],['ATTACKED','بعد الهجوم'],['ASR / COUNTS','نجاح الهجوم / الأعداد'],
    ['MEAN L0 / L2 / L∞','متوسط L0 / L2 / L∞'],['PROVENANCE / CROSS-CHECK','المصدر / التحقق المستقل'],
    ['No completed results match these filters. Choose another attack or norm.','مفيش نتائج مكتملة مطابقة للفلاتر دي. اختار هجوم أو مقياس تاني.'],
    ['No epsilon curve applies.','مفيش منحنى ε للحالة دي.'],
    ['CleverHans: Not run','CleverHans: لسه متنفّذش'],
    ['MODELS & DATA / SPRINT 05','الموديلات والداتا / SPRINT 05'],
    ['SOURCE SAMPLES','عينات المصدر'],['BASELINE MODELS','الموديلات الأساسية'],
    ['BEST VALIDATION ACCURACY','أحسن دقة على التحقق'],['VALIDATION SAMPLES','عينات التحقق'],
    ['Measured development runs','تجارب تطوير مقاسة'],['Held-out test remains untouched','الاختبار المحجوز مش مستخدم هنا'],
    ['Baseline performance','أداء الموديلات الأساسية'],['VALIDATION ONLY','تحقق فقط'],
    ['The data foundation','أساس البيانات'],['Model comparison','مقارنة الموديلات'],['LIVE ARTIFACTS','نتائج مسجّلة متاحة'],
    ['Training split','تقسيم التدريب'],['Validation split','تقسيم التحقق'],['Official test split','تقسيم الاختبار الرسمي'],
    ['Available labeled records','السجلات المصنّفة المتاحة'],['Time-based split','تقسيم حسب الزمن'],['Reserved for gated evaluation','محجوز للتقييم بعد الاعتماد'],
    [' training rows used in this comparison.',' عينة تدريب مستخدمة في المقارنة دي.'],[' Results are developmental.',' النتائج للتطوير.'],
    ['Research boundaries','حدود البحث'],
    ['Historical Sprint 3 development comparison; these uncalibrated scores do not describe the Sprint 4 candidate. Open Attack comparison for Sprint 5 results. Executable scanning and production deployment remain outside the current implementation.','مقارنة تطوير تاريخية من Sprint 3؛ الدرجات دي غير معايرة ومش بتوصف موديل Sprint 4. افتح مقارنة الهجمات لنتائج Sprint 5. فحص ملفات تنفيذية والتشغيل الإنتاجي مش ضمن التنفيذ الحالي.'],
    ['BEST ACCURACY','أعلى دقة'],['FALSE POSITIVES','الإنذارات الكاذبة'],['Accuracy','الدقة'],['F1 score','مقياس F1'],
    ['Experiment batch','دفعة التجارب'],['Same dataset · same rows · same split','نفس الداتا · نفس العينات · نفس التقسيم'],
    ['Validation leaderboard','ترتيب نتائج التحقق'],['Performance comparison','مقارنة الأداء'],['INDIVIDUAL METRICS','المقاييس بالتفصيل'],['Run details','تفاصيل التجربة'],
    ['Training rows','عينات التدريب'],['Validation rows','عينات التحقق'],['Seed','بذرة العشوائية'],['Training subset','جزء من بيانات التدريب'],['Full training split','كل تقسيم التدريب'],['validation only','تحقق فقط'],['test not evaluated','الاختبار متقيّمش'],['test evaluated','الاختبار اتقيّم'],
    ['Actual class → predicted class · exact counts','الفئة الحقيقية ← توقّع الموديل · أعداد فعلية'],
    ['Benign → benign','سليم ← سليم'],['Benign → malicious (false alarm)','سليم ← ضار (إنذار كاذب)'],['Malicious → benign (missed)','ضار ← سليم (تفويت)'],['Malicious → malicious','ضار ← ضار'],
    ['Scores are model estimates, not guarantees that a file is safe. A decision margin is used for Linear SVM.','الدرجات تقديرات من الموديل، مش ضمان لأمان الملف. Linear SVM بيستخدم هامش قرار.'],
    ['SOURCE RECORDS','سجلات المصدر'],['FEATURE DIMENSIONS','عدد الخصائص'],['PROCESSING SCOPE','نطاق المعالجة'],['LOCAL VERIFICATION','التحقق المحلي'],['Recorded EDA report','تقرير استكشاف مسجّل'],['Numeric feature representation','تمثيل رقمي للخصائص'],['Recorded manifest','بيان بيانات مسجّل'],['Not checked','متراجعش'],['Use the preprocessing CLI','استخدم أمر تجهيز الداتا'],
    ['Time-based validation. Official test set preserved.','تحقق حسب الزمن. الاختبار الرسمي محفوظ.'],['Binary-stratified random split; rare classes may be absent.','تقسيم عشوائي موزون للفئتين؛ الفئات النادرة ممكن متظهرش.'],
    ['These are recorded dataset reports, not a fresh verification of local arrays.','دي تقارير مسجّلة عن الداتا، مش تحقق جديد من الملفات المحلية.'],['Manifest, cleaning and feature metadata','بيان الداتا والتنظيف ومعلومات الخصائص'],['Unlabeled','غير مصنّف'],['Subset','جزء من الداتا'],['Full','كامل'],
    ['EVIDENCE & LIMITATIONS','الأدلة والقيود'],['MNIST environment check only. These results do not measure EMBER malware robustness.','دي تجربة تجهيز الأدوات على MNIST بس؛ مش قياس لمقاومة موديل EMBER.'],['CLEAN MNIST ACCURACY','دقة MNIST قبل الهجوم'],['Recorded Sprint 1 tooling run','تجربة أدوات مسجّلة في Sprint 1'],['SEED','بذرة العشوائية'],['Reproducible run configuration','إعدادات لإعادة التجربة'],['TRAINING EPOCHS','دورات التدريب'],['MNIST demonstration','تجربة MNIST'],['DOMAIN','نوع الداتا'],['Separate from malware detection','منفصل عن كشف الملفات الضارة'],['Attack tooling results','نتائج أدوات الهجوم'],['Recorded accuracy under attack','الدقة المسجّلة تحت الهجوم'],['Loading figure…','بنحمّل الرسم…'],
    ['Frozen baseline · feature prediction (Sprint 4)','الموديل المعتمد · توقّع الخصائص (Sprint 4)'],
    ['The comparison tables above retain Sprint 3 validation-only results. For Sprint 4 evaluation and M1 status, open Methodology → sprint4, or load the frozen identity below.','الجداول فوق فيها نتائج التحقق التاريخية لـSprint 3. لتقييم Sprint 4 وحالة M1، افتح المنهجية ← sprint4، أو حمّل هوية الموديل المعتمد تحت.'],
    ['Public EMBER2018 v2 feature rows only. No executable or PCAP uploads. Scores are research estimates, not file-safety guarantees. Prediction remains unavailable until M1 passes.','خصائص EMBER2018 v2 العامة بس. مفيش رفع ملفات تنفيذية أو PCAP. الدرجات تقديرات بحثية، مش ضمان لأمان الملف. التوقّع مش متاح لحد اعتماد M1.'],
    ['Prediction access token (not saved)','رمز وصول التوقّع (مش بيتحفظ)'],['Load frozen model identity','حمّل هوية الموديل المعتمد'],['Feature representation','تمثيل الخصائص'],['Raw EMBER feature values','قيم خصائص EMBER الخام'],["Already signed-log1p standardized with this model's scaler",'قيم متحوّلة ومعيارية بنفس تحويل الموديل'],['Ordered numeric rows as JSON (1–32 rows × 2381 features)','صفوف أرقام مرتّبة بصيغة JSON (1–32 صف × 2381 خاصية)'],['Predict features','صنّف الخصائص'],
    ['Read the numbers','افهم الأرقام'],['Accuracy:','الدقة:'],['ASR:','نسبة نجاح الهجوم:'],['Perturbations:','التعديلات:'],['Constraints:','القيود:'],['Cross-check:','التحقق المستقل:'],
    [' correct decisions ÷ all evaluated rows. Clean and attacked scores use the same rows.',' القرارات الصح ÷ كل العينات المختبرة. قبل الهجوم وبعده على نفس العينات.'],
    [' originally correct decisions made incorrect ÷ originally correct decisions. Both benign and malicious rows are included; this is untargeted error induction, not a malware-only evasion rate. An empty denominator is unavailable.',' القرارات الصحيحة اللي اتحوّلت لغلط ÷ القرارات الصحيحة أصلًا. الفئتين داخلين في الحساب؛ مش نسبة تفويت ملفات ضارة بس. المقام الفاضي نتيجته غير متاحة.'],
    [' mean L0 (changed coordinates above 10⁻⁶), L2 and L∞ across all evaluated rows, in signed-log1p standardized model coordinates. Epsilon is not a percentage or a raw byte budget.',' متوسط L0 (الخصائص المتغيرة فوق 10⁻⁶) وL2 وL∞ لكل العينات على إحداثيات الموديل المعيارية. ε مش نسبة مئوية ولا ميزانية بايتات خام.'],
    [' bounds, immutable masks and integer counts are feature-space approximations. They do not establish a valid executable. CW-L2 is projected after generation and is not a constrained optimum.',' الحدود والخصائص الثابتة وتقريب الأعداد الصحيحة قيود في مساحة الخصائص؛ مش إثبات لملف تنفيذي صالح. CW-L2 بيتراجع للقيود بعد التوليد، ومش حل مثالي مقيّد.'],
    [' CleverHans is an independent implementation; matching metrics alone do not prove equivalent attacks. Missing checks remain “Not run”. No experiments run from this page.',' CleverHans تنفيذ مستقل؛ تطابق المقاييس مش إثبات إن الهجمات متكافئة. التحقق الناقص يفضل «متنفّذش». مفيش تجارب بتشتغل من الصفحة دي.'],
  ];
  const escapeRegex = s => s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const converters = new Map();
  function translate(text, language) {
    if (!converters.has(language)) {
      const from = language === 'ar' ? 0 : 1, to = 1-from, map = new Map();
      copy.forEach(pair => { if (!map.has(pair[from])) map.set(pair[from],pair[to]); });
      const patterns = [...map.keys()].sort((a,b)=>b.length-a.length).map(key =>
        `${/^[A-Za-z]/.test(key) ? '(?<![A-Za-z])' : ''}${escapeRegex(key)}${/[A-Za-z]$/.test(key) ? '(?![A-Za-z-])' : ''}`);
      converters.set(language,{map,pattern:new RegExp(patterns.join('|'),'g')});
    }
    const {map,pattern} = converters.get(language);
    return text.replace(pattern, match => map.get(match));
  }
  if (typeof module !== 'undefined') module.exports = {translate};
  if (typeof document === 'undefined') return;
  let language = 'en';
  try { if (localStorage.getItem('arsm-language') === 'ar') language = 'ar'; } catch (_) { /* Storage may be disabled. */ }
  const originals = new WeakMap();
  const attributeOriginals = new WeakMap();
  const originalTitle = document.title;
  const switcher = document.createElement('div');
  switcher.className = 'language-switch';
  switcher.setAttribute('role','group'); switcher.setAttribute('aria-label','Interface language');
  switcher.innerHTML = '<button type="button" data-language="en" lang="en">English</button><button type="button" data-language="ar" lang="ar">مصري</button>';
  document.querySelector('header').append(switcher);
  function apply() {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title = translate(originalTitle,language);
    const walker = document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let node;
    while ((node=walker.nextNode())) {
      if (!node.textContent.trim() || node.parentElement.closest('script,style,pre,code,.language-switch,[data-release]')) continue;
      let record = originals.get(node);
      if (!record || node.textContent !== record.rendered) record = {original:node.textContent};
      record.rendered = translate(record.original,language);
      originals.set(node,record);
      if (node.textContent !== record.rendered) node.textContent = record.rendered;
    }
    document.querySelectorAll('[aria-label],[title],[placeholder]').forEach(element => {
      const records = attributeOriginals.get(element) || {};
      for (const name of ['aria-label','title','placeholder']) {
        if (!element.hasAttribute(name)) continue;
        let record = records[name];
        const value = element.getAttribute(name);
        if (!record || value !== record.rendered) record = {original:value};
        record.rendered = translate(record.original,language);
        records[name] = record;
        if (value !== record.rendered) element.setAttribute(name,record.rendered);
      }
      attributeOriginals.set(element,records);
    });
    switcher.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed',String(button.dataset.language===language)));
  }
  switcher.querySelectorAll('button').forEach(button => button.onclick = () => {
    language = button.dataset.language;
    try { localStorage.setItem('arsm-language',language); } catch (_) { /* Keep session choice. */ }
    apply();
    document.dispatchEvent(new Event('arsm-language'));
  });
  let scheduled=false;
  new MutationObserver(() => {
    if (scheduled) return;
    scheduled=true;
    queueMicrotask(() => { scheduled=false; apply(); });
  }).observe(document.body,{subtree:true,childList:true,characterData:true});
  apply();
})();
