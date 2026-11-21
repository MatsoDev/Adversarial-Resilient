'use strict';
// Translate interface prose, never raw research reports, identifiers or JSON.
(() => {
  const copy = [
    ['ARSM · Research overview','ARSM · نظرة عامة على البحث'],
    ['ARSM · Attack comparison','ARSM · مقارنة الهجمات'],
    ['Research overview and a recorded adversarial feature-space experiment.','نظرة عامة على البحث وتجربة مسجّلة لهجوم في feature space.'],
    ['Recorded exploratory attack results, comparison conditions and research limitations.','نتائج هجمات استكشافية مسجّلة، وشروط المقارنة، وحدود البحث.'],
    ['Historical model validation, dataset provenance, methods and gated feature prediction.','نتائج التحقق التاريخية للنماذج، ومصدر البيانات، والمنهجية، والتنبؤ المشروط بالخصائص.'],
    ['Threat assumptions, transfer evidence and feature-space realism limitations.','افتراضات التهديد، وأدلة transfer، وحدود الواقعية في feature space.'],
    ['RESEARCH PROJECT','مشروع بحثي'],
    ['Research overview','نظرة عامة على البحث'],
    ['Recorded research evidence','أدلة بحثية مسجّلة'],
    ['ARSM / Research overview','ARSM / نظرة عامة على البحث'],
    ['Research status','حالة البحث'],
    ['Exploratory, feature-space only · Real transfer pending · Frozen benchmark not yet accepted · Defenses planned','استكشافي ضمن feature space فقط · transfer: القياس الفعلي قيد الانتظار · frozen benchmark: لم يُعتمد بعد · الدفاعات مخطَّط لها'],
    ['Adversarial resilience in malware detection','متانة كشف البرمجيات الضارة أمام adversarial attacks'],
    ["This project studies machine-learning malware detectors using numeric features extracted from files. Adversarial examples are deliberately modified inputs used to test whether a model's decision changes. The recorded experiments evaluate these changes in feature space, not on executable files.",'يدرس المشروع كواشف البرمجيات الضارة القائمة على التعلّم الآلي باستخدام خصائص رقمية مستخرجة من الملفات. وتُعدّ adversarial examples مدخلات تُعدّل عمدًا لاختبار تغيّر قرار النموذج. تُقيّم التجارب المسجّلة هذه التعديلات في feature space، لا على ملفات تنفيذية.'],
    ['Research method','منهجية البحث'],
    ['01 / MODEL','01 / النموذج'],['02 / EVALUATE','02 / التقييم'],['03 / FUTURE WORK','03 / العمل المستقبلي'],
    ['Train a detector','تدريب كاشف'],
    ['Learn from feature records with known benign or malicious labels.','يتعلّم الكاشف من سجلات خصائص ذات تصنيفات مرجعية معروفة، ضارة أو غير ضارة.'],
    ['Test model decisions','اختبار قرارات النموذج'],
    ['Measure whether allowed feature changes turn correct decisions into errors.','نقيس ما إذا كانت التعديلات المسموح بها للخصائص تحوّل القرارات الصحيحة إلى أخطاء.'],
    ['Evaluate defenses','تقييم الدفاعات'],
    ['Defense methods and comparative evaluations are planned; results are not yet available.','تُخطّط وسائل الدفاع والتقييمات المقارنة لمرحلة لاحقة؛ ولا تتوافر نتائجها بعد.'],
    ['Recorded case study','دراسة حالة مسجّلة'],
    ['Recorded case catalogue','فهرس الحالات المسجّلة'],
    ['Browse cases in the selected experiment. The link identifies the recorded run, configuration and sample.','تصفّح حالات التجربة المختارة. الرابط يحدّد التشغيل والإعدادات والعينة المسجّلة.'],
    ['Filter by method, norm, seed, outcome, or row','تصفية حسب الطريقة أو المعيار أو البذرة أو النتيجة أو رقم الصف'],
    ['Export matching cases as CSV','تصدير الحالات المطابقة بصيغة CSV'],
    ['Or select a JSON file of numeric feature rows','أو اختر ملف JSON يحتوي على صفوف خصائص رقمية'],
    ['A successful file submission records the batch results locally. Clear the file selection to classify pasted rows.','عند نجاح إرسال الملف، تُحفظ نتائج الدفعة محليًا. ألغِ اختيار الملف لتصنيف الصفوف الملصقة.'],
    ['Load batch history','عرض سجل الدفعات'],
    ['Export history CSV','تصدير السجل بصيغة CSV'],
    ['matching recorded cases','حالة مسجّلة مطابقة'],
    ['The linked case is unavailable. Choose another recorded case from the catalogue.','الحالة المرتبطة غير متاحة. اختار حالة مسجّلة أخرى من الفهرس.'],
    ['A three-step replay shows the original classification, a feature change, and the resulting decision. No experiment is executed in the browser.','يعرض شرح من ثلاث خطوات التصنيف الأصلي، وتعديل الخصائص، والقرار الناتج. ولا تُشغّل تجربة في المتصفح.'],
    ['View the recorded case','استعراض الحالة المسجّلة'],
    ['Dataset and interpretation','البيانات وتفسير النتائج'],
    ['EMBER feature records','سجلات خصائص EMBER'],
    ['EMBER contains numeric descriptions extracted from Windows programs, with known labels where available. Each sample is one feature record; the original program is not executed.','تضم EMBER أوصافًا رقمية مستخرجة من برامج Windows، مع التصنيفات المرجعية حيث تتوافر. تمثّل كل عينة سجل خصائص واحدًا؛ ولا يُشغّل البرنامج الأصلي.'],
    ['Research use and scope','استخدام البحث ونطاقه'],
    ['These tests help researchers assess detector decisions under specified conditions. The prototype is not a complete antivirus product.','تساعد الاختبارات الباحثين في تقييم قرارات الكاشف ضمن شروط محدّدة. والنموذج البحثي ليس منتجًا متكاملًا لمكافحة الفيروسات.'],
    ['Limits of an individual case','حدود الحالة الفردية'],
    ['A selected case illustrates one outcome. Aggregate results describe the evaluated cohort under the specified model, sample selection and constraints; neither establishes a valid executable modification.','توضّح الحالة المختارة نتيجة واحدة. وتصف النتائج المجمّعة cohort وفق النموذج والعينات والقيود المحدّدة؛ ولا تثبت أيٌّ منهما صلاحية تعديل ملف تنفيذي.'],
    ['Evaluation objective','هدف التقييم'],
    ['Clean accuracy alone does not establish robustness. This study measures attack-induced errors; future work will evaluate defenses and their effect on ordinary performance.','لا تثبت الدقة قبل الهجوم وحدها متانة النموذج. تقيس الدراسة الأخطاء التي أحدثتها الهجمات؛ وسيقيّم العمل المستقبلي الدفاعات وأثرها على الأداء في الظروف العادية.'],
    ['View attack results and methodology','استعراض نتائج الهجمات والمنهجية'],
    ['Recorded model decisions before and after feature-space attacks, with the conditions required for comparison.','قرارات النموذج المسجّلة قبل هجمات feature space وبعدها، وشروط المقارنة بينها.'],
    ['Experiment and attack filters','خيارات التجربة والهجوم'],
    ['Filter results','تصفية النتائج'],['Reset filters','إعادة ضبط عوامل التصفية'],
    ['Exploratory · feature space','استكشافي · feature space'],
    ['Historical validation','تحقق تاريخي'],
    ['Feature prediction','التنبؤ بالخصائص'],
    ['Gated · authentication and a verified frozen model required','مقيّد · يتطلّب المصادقة والتحقق من frozen model'],
    ['Prediction requirements and controls','متطلبات التنبؤ وأدواته'],
    ['Recorded white-box results and available transfer evidence, with the limits of feature-space evaluation.','نتائج white-box المسجّلة وأدلة transfer المتاحة، مع حدود التقييم في feature space.'],
    ['Recorded classification case','حالة تصنيف مسجّلة'],
    ['Original classification','التصنيف الأصلي'],
    ['The model prediction is compared with the reference label to establish whether the initial decision was correct.','يُقارن تنبؤ النموذج بالتصنيف المرجعي لتحديد صحة القرار الأولي.'],
    ['The initial decision matched the reference label.','طابق القرار الأولي التصنيف المرجعي.'],
    ['The initial decision was incorrect; this is not an attack-induced error.','كان القرار الأولي خاطئًا؛ وهذا ليس خطأً أحدثه الهجوم.'],
    ['Feature-space modification','التعديل في feature space'],
    ['The attack searches for an allowed feature change that produces an incorrect decision. The values below were recorded previously; no experiment runs in the browser.','يبحث الهجوم عن تعديل مسموح للخصائص ينتج عنه قرار خاطئ. القيم أدناه مسجّلة مسبقًا؛ ولا تُشغّل تجربة في المتصفح.'],
    ['Recorded feature changes','تغيّرات الخصائص المسجّلة'],
    ['Interpretation of the recorded change','تفسير التعديل المسجّل'],
    ['Interpretation of model scores','تفسير درجات النموذج'],
    ['Case interpretation','تفسير الحالة'],
    ['Interpretation limits','حدود التفسير'],
    ['A selected case illustrates one outcome. The evaluated cohort measures its frequency under the specified model, sampling and constraints.','توضّح الحالة المختارة نتيجة واحدة. وتقيس cohort تكرارها وفق النموذج والعينات والقيود المحدّدة.'],
    ['Results for the evaluated cohort','نتائج cohort المُقيّمة'],
    ['Planned · not yet evaluated','مخطّط · لم يُقيّم بعد'],
    ['Defense evaluation','تقييم الدفاعات'],
    ['The model initially detected this malicious sample, then classified it as benign after the feature change. The attack changed the decision for this feature record.','اكتشف النموذج العينة الضارة أولًا، ثم صنّفها غير ضارة بعد تعديل الخصائص. غيّر الهجوم القرار لهذا السجل من الخصائص.'],
    ['Model validation','التحقق من النماذج'],
    ['Historical validation results, dataset records and research methods.','نتائج التحقق التاريخية وسجلات البيانات ومنهجية البحث.'],
    ['Compare recorded performance on the same validation data.','مقارنة الأداء المسجّل على بيانات التحقق نفسها.'],
    ['Dataset records','سجلات البيانات'],
    ['Dataset composition, preparation and provenance.','تركيب البيانات وإعدادها ومصدرها.'],
    ['Research methodology','منهجية البحث'],
    ['Threat assumptions, feature constraints and research limitations.','افتراضات التهديد، وقيود الخصائص، وحدود البحث.'],
    ['MNIST tooling demonstration','عرض أدوات الاختبار على MNIST'],
    ['Historical model validation metrics','مقاييس التحقق التاريخية للنماذج'],
    ['Historical validation accuracy, F1 and ROC-AUC are shown for each model. Exact values appear in the model table.','يعرض الرسم دقة التحقق التاريخية وF1 وROC-AUC لكل نموذج. ترد القيم الدقيقة في جدول النماذج.'],
    ['Scroll the chart horizontally to view all models.','مرّر الرسم أفقيًا لاستعراض جميع النماذج.'],
    ['Scrollable model comparison chart','رسم مقارنة النماذج القابل للتمرير'],
    ['Scroll the table horizontally to view all columns.','مرّر الجدول أفقيًا لاستعراض جميع الأعمدة.'],
    ['Data table','جدول البيانات'],
    ['No recorded individual cases are available. Aggregate results may be available in Attack comparison.','لا تتوافر حالات فردية مسجّلة. قد تتوافر نتائج مجمّعة في مقارنة الهجمات.'],
    ['Selected case studies are available in the research overview when recorded.','تتاح دراسات الحالات المختارة في نظرة عامة على البحث عند تسجيلها.'],
    ['Measured results table and provenance','جدول النتائج المقاسة ومصدرها'],
    ['Accuracy is measured on the same selected rows before and after attack; ε is in standardized model coordinates.','تُقاس الدقة على الصفوف المختارة نفسها قبل الهجوم وبعده؛ وتُعبّر ε عن إحداثيات النموذج المعيارية.'],
    ['Dashed black line: accuracy before attack. Series use distinct line patterns; exact values and counts are in the results table.','يمثّل الخط الأسود المتقطّع الدقة قبل الهجوم. تستخدم السلاسل أنماط خطوط مختلفة؛ وترد القيم والأعداد الدقيقة في جدول النتائج.'],
    [' A feature change does not establish a valid executable modification.',' لا يثبت تغيير خاصية صلاحية تعديل ملف تنفيذي.'],
    ['Transfer results pending','نتائج transfer قيد الانتظار'],
    ['Feature changes do not establish a valid executable modification or preserved behavior.','لا تثبت تعديلات الخصائص صلاحية تعديل ملف تنفيذي أو الحفاظ على سلوكه.'],
    ['Recorded white-box results are not black-box evidence.','نتائج white-box المسجّلة ليست دليلًا على black-box.'],
    ['Historical Sprint 1 attack_success_rate fields are overall adversarial error rates, not the conditional ASR used in current experiments.','تمثّل حقول attack_success_rate التاريخية في المرحلة 1 معدّلات الخطأ الإجمالية بعد الهجوم، وليست ASR المشروط المستخدم في التجارب الحالية.'],
    ['The figure plots recorded MNIST accuracy across the listed attack strengths; exact values follow.','يوضّح الرسم دقة MNIST المسجّلة عند مقادير الهجوم المدرجة؛ وترد القيم الدقيقة أدناه.'],
    ['MNIST accuracy by attack strength','دقة MNIST حسب مقدار الهجوم'],
    ['No recorded MNIST curve data is available.','لا تتوافر بيانات مسجّلة لمنحنى MNIST.'],
    ['Epsilon','ε'],
    ['FGSM accuracy','دقة FGSM'],
    ['PGD accuracy','دقة PGD'],
    ['ARSM · AI deception journey','ARSM · رحلة التعلّم الآلي والتضليل'],
    ['ARSM · Models and data','ARSM · النماذج والبيانات'],
    ['ARSM · Attack results','ARSM · نتائج الهجمات'],
    ['ARSM · Threat context and transfer','ARSM · سياق التهديد وtransfer'],
    ['Adversarial-Resilient Security Models','نماذج أمنية تقاوم adversarial attacks'],
    ['ARSM dashboard','الصفحة الرئيسية للمشروع'],
    ['Skip to content','انتقل إلى المحتوى'],
    ['Interface language','لغة الواجهة'],
    ['Main navigation','التنقل الرئيسي'],
    ['Research views','واجهات البحث'],
    ['Attack families and budgets','خوارزميات الهجوم وحدود التعديل'],
    ['FGSM (Fast Gradient Sign Method) takes one gradient step. PGD (Projected Gradient Descent) repeats steps with projection. CW-L2 (Carlini–Wagner) optimizes L2 distortion; this project applies the policy after generation.','تستخدم طريقة إشارة التدرّج السريع (FGSM) خطوة تدرّج واحدة، ويكرّر الانحدار المتدرّج مع الإسقاط (PGD) الخطوات مع تطبيق القيود. أمّا هجوم كارليني–واغنر (CW-L2) فيبحث عن تعديل وفق مقياس L2؛ ويطبّق المشروع سياسة القيود بعد توليده.'],
    ['Metric definitions','تعريف المقاييس'],
    ['feature version','إصدار الخصائص'],
    ['Source documents are retained in their recorded language for technical reference.','تُعرض الوثائق بلغتها المسجّلة للرجوع التقني، دون ترجمة نصوص الأدلة الأصلية.'],
    ['AI resilience lab','مختبر متانة التعلّم الآلي'],
    ['AI deception journey','رحلة التعلّم الآلي والتضليل'],
    ['← AI journey','← رحلة التجربة'],
    ['AI journey','رحلة التجربة'],
    ['Attack comparison','مقارنة الهجمات'],
    ['Models and data','النماذج والبيانات'],
    ['Models & data','النماذج والبيانات'],
    ['Threat context and transfer','سياق التهديد وtransfer'],
    ['Recorded research experiments','تجارب بحثية مسجّلة'],
    ['Same release = same team starting point','إصدار موحّد لعرض أدلة البحث'],
    ['ARSM / Understand the experiment','ARSM / فهم التجربة'],
    ['GRADUATION RESEARCH / ADVERSARIAL MACHINE LEARNING','مشروع تخرّج · بحث في متانة التعلّم الآلي'],
    ['Can a security model resist deception?','هل يمكن تضليل نموذج للكشف الأمني؟'],
    ['We study malware detection through numeric file features. Controlled adversarial tests reveal where machine-learning decisions fail—and what the evidence does not yet establish.','ندرس كشف البرمجيات الضارة عبر خصائص الملفات الرقمية. وتبيّن اختبارات adversarial المضبوطة مواضع إخفاق قرارات التعلّم الآلي، وحدود ما تثبته الأدلة الحالية.'],
    ['How this project works','منهجية المشروع'],
    ['01 / TRAIN','01 / التدريب'],['02 / CHALLENGE','02 / الاختبار'],['03 / IMPROVE','03 / التحسين المخطّط'],
    ['Teach it the difference','تعلّم التمييز بين الفئتين'],
    ['Learn from examples with known benign or malicious labels.','يتعلّم النموذج من أمثلة ذات تصنيفات مرجعية معروفة: ضارة أو غير ضارة.'],
    ['Try to change its answer','اختبار ثبات القرار'],
    ['Change allowed input features and check whether a correct answer becomes wrong.','نعدّل خصائص الإدخال ضمن القيود المسموح بها، ونقيس تحوّل القرارات الصحيحة إلى أخطاء.'],
    ['Measure, then strengthen','القياس قبل تعزيز المتانة'],
    ['Count the failures. Later, add defenses and repeat the test to measure improvement.','نقيس الأخطاء أولًا. وفي مرحلة لاحقة، نضيف وسائل دفاع ونعيد الاختبار لقياس التحسّن، إن وُجد.'],
    ['Defense work is planned for Sprints 9–12.','أعمال الدفاع مخطّطة للمراحل 9–12، ولم تُقَس نتائجها بعد.'],
    ['Now see one real example.','استكشف حالة مقاسة خطوة بخطوة.'],
    ['Three short steps. No AI knowledge needed. You are replaying a recorded experiment.','ثلاث خطوات لفهم تجربة مسجّلة، دون الحاجة إلى معرفة مسبقة بالتعلّم الآلي.'],
    ['Start the walkthrough ↓','ابدأ شرح الحالة ↓'],
    ['We test ','نختبر '],['features extracted from files','خصائص مستخرجة من ملفات'],
    [', without executing them. This is not an antivirus scan or proof of a valid file modification.',' دون تشغيلها. هذا ليس فحصًا لمكافحة الفيروسات، ولا إثباتًا لإمكان تعديل ملف تنفيذي صالح.'],
    ['Choose a different experiment, attack or case','اختيار تجربة أو هجوم أو حالة أخرى'],
    ['The first recorded successful case is selected when available. No attacks or training are executed from this page.','تُعرض أول حالة ناجحة مسجّلة عند توافرها. ولا تُشغّل هذه الصفحة هجمات أو تدريبًا.'],
    ['Experiment','التجربة'],['Attack and parameters','الهجوم ومعاملاته'],['Selected case','الحالة المختارة'],
    ['Loading measured results…','جارٍ تحميل النتائج المقاسة…'],
    ['The questions behind the project','أسئلة لفهم البحث'],
    ['What is EMBER, and what is a sample?','ما مجموعة EMBER؟ وما المقصود بالعينة؟'],
    ["EMBER contains numeric descriptions extracted from Windows programs, with known labels where available. A sample here is one description, like a file's information card. We do not run the original program.",'تضم EMBER أوصافًا رقمية مستخرجة من برامج Windows، مع التصنيفات المرجعية حيث تتوافر. والعينة هنا وصف رقمي واحد لبرنامج، لا البرنامج نفسه؛ ولا نشغّل الملفات الأصلية.'],
    ['Who would use this, and why?','لمن يفيد هذا البحث؟'],
    ['Security researchers and teams building AI detectors can use these tests to find weaknesses and compare model versions before deployment. This research prototype is not a complete antivirus product.','تفيد هذه الاختبارات باحثي الأمن ومطوّري نماذج الكشف في تحديد نقاط الضعف ومقارنة النماذج قبل النشر. المشروع نموذج بحثي، وليس نظامًا متكاملًا لمكافحة البرمجيات الضارة.'],
    ['Did we actually change a malware file?','هل عُدّل ملف ضار فعليًا؟'],
    ['No. This experiment changes recorded feature values only. A decision change does not prove that a valid executable could be modified in the same way.','لا. تعدّل التجربة قيم الخصائص المسجّلة فقط. وتغيّر قرار النموذج لا يثبت إمكان إجراء تعديل مماثل على ملف تنفيذي صالح.'],
    ['Does one fooled example prove the whole model is bad?','هل تكفي حالة تضليل واحدة للحكم على النموذج؟'],
    ['No. A case explains what happened once. The larger experiment measures how often it happened, under the exact model, sample selection and constraints shown.','لا. تشرح الحالة نتيجة واحدة؛ أما التجربة المجمّعة فتقيس تكرارها ضمن النموذج والعينات والقيود المحدّدة.'],
    ['What are we trying to establish?','ما السؤال البحثي؟'],
    ['High accuracy alone is not enough. We test whether an attack changes correct decisions, then measure whether defenses help without damaging normal performance.','لا تكفي الدقة العالية وحدها. نختبر قدرة الهجمات على تغيير القرارات الصحيحة، ونخطّط لاحقًا لقياس أثر الدفاعات مع الحفاظ على الأداء في الظروف العادية.'],
    ['Open the numbers and research details →','استعرض النتائج والتفاصيل البحثية ←'],
    ['Recorded example walkthrough','شرح حالة مسجّلة'],
    ['A file description. One decision. One challenge.','وصف رقمي، وقرار، واختبار للمتانة.'],
    ['Walkthrough steps','خطوات شرح الحالة'],
    ['1 · Original sample','1 · العينة الأصلية'],['2 · The change','2 · التعديل'],['3 · The result','3 · النتيجة'],
    ['STEP 1 OF 3','الخطوة 1 من 3'],['STEP 2 OF 3','الخطوة 2 من 3'],['STEP 3 OF 3','الخطوة 3 من 3'],
    ['First, check the answer before any attack.','نبدأ بالتحقق من القرار قبل الهجوم.'],
    ['The dataset tells us the known label. The AI makes its own prediction. Comparing the two tells us whether the AI started out correct.','نقارن توقّع النموذج بالتصنيف المرجعي المسجّل في مجموعة البيانات، لنعرف هل كان القرار صحيحًا قبل الهجوم.'],
    ['Benign means non-malicious. Malicious means labelled as malware. A model prediction is not a file-safety guarantee.','«غير ضار» و«ضار» تصنيفان في البيانات. ولا يمثّل توقّع النموذج ضمانًا لسلامة الملف.'],
    ['The AI got this example right. Next, we will challenge that decision.','كان قرار النموذج صحيحًا في هذه الحالة. ننتقل الآن إلى اختبار ثباته.'],
    ['The AI was already wrong here. Keep that in mind: this is not an attack-induced error.','كان القرار خاطئًا أصلًا؛ لذا لا تُنسب هذه الحالة إلى نجاح الهجوم.'],
    ['Change the description, then ask the AI again.','نعدّل الوصف الرقمي ثم نعيد التصنيف.'],
    ['An adversarial attack deliberately looks for an allowed change that makes the model answer incorrectly. We replay the measured change below; no experiment runs in your browser.','يبحث adversarial attack عن تعديل مسموح يدفع النموذج إلى قرار خاطئ. نعرض هنا التعديل المقاس في تجربة سابقة؛ ولا تُشغّل تجربة في المتصفح.'],
    ['What this means in this experiment','تفسير التعديل في هذه التجربة'],
    ['Only the listed numeric features changed. For this size-only probe, all other 2,380 coordinates stayed fixed. The raw size values above are approximate bytes, reconstructed from the measured model inputs.','تغيّرت الخصائص الرقمية المدرجة فقط. وفي هذا الاختبار الخاص بالحجم، بقيت الخصائص الأخرى وعددها 2,380 ثابتة. قيم الحجم بالبايت تقريبية، وأُعيد بناؤها من مدخلات النموذج المقاسة.'],
    ['Only the listed numeric features changed above the measurement tolerance. Raw values are approximate inverse transforms of the measured model inputs.','لم يتجاوز حدّ سماحية القياس سوى التغيّر في الخصائص المدرجة. والقيم الخام تقريبية، ناتجة عن عكس التحويل المستخدم لمدخلات النموذج.'],
    ['This recorded attempt produced no feature change above the measurement tolerance. That is a real outcome too.','لم تُنتج المحاولة المسجّلة تغيّرًا يتجاوز حدّ سماحية القياس. وهذه نتيجة مقاسة أيضًا.'],
    ['No bytes in an actual file were changed. We are testing the model on feature descriptions.','لم تُعدّل بايتات أي ملف فعلي؛ الاختبار يجري على الأوصاف الرقمية للخصائص.'],
    ['Technical attack settings','الإعدادات التقنية للهجوم'],
    ['Why does this matter?','ما أهمية ذلك؟'],
    ['This test helps engineers find where an AI detector can fail. They can then compare a stronger version under the same conditions. One case explains a failure; the whole cohort measures its frequency.','يساعد الاختبار في تحديد مواضع إخفاق الكاشف، تمهيدًا لمقارنة نموذج محسّن تحت الشروط نفسها. تشرح الحالة إخفاقًا واحدًا، وتقيس cohort مدى تكراره.'],
    ['How often did this happen in the experiment?','ما مدى تكرار النتيجة في التجربة؟'],
    ['Previous step','الخطوة السابقة'],['Next: feature change →','التالي: تعديل الخصائص ←'],['Next: classification result →','التالي: نتيجة التصنيف ←'],['Restart case replay ↻','أعد عرض الحالة ↻'],
    ['Model score','درجة النموذج'],['How should I read the scores?','كيف تُفسّر درجات النموذج؟'],
    ['Successful attack','هجوم ناجح'],['Remained correct','بقي القرار صحيحًا'],['Preexisting error','خطأ سابق للهجوم'],
    ['The model was already wrong. This case is not evidence of a successful attack and is excluded from the ASR denominator.','كان قرار النموذج خاطئًا قبل الهجوم. لا تثبت هذه الحالة نجاح الهجوم، وتُستبعد من مقام ASR.'],
    ['The model stayed correct after this attempt. That is one resisted case, not a guarantee against every attack.','بقي التصنيف صحيحًا بعد المحاولة. هذا ثبات في حالة واحدة، وليس ضمانًا لمقاومة جميع الهجمات.'],
    ['The model initially detected this malicious sample, then called it benign after the feature change. This attempt successfully fooled the decision on this feature row.','اكتشف النموذج العينة الضارة أولًا، ثم صنّفها غير ضارة بعد تعديل الخصائص. نجحت المحاولة في تضليل القرار على هذا الصف من البيانات.'],
    ['This sample is benign. The model was initially correct, but the change caused a malicious verdict: a false alarm, not malware escaping detection.','العينة غير ضارة وكان تصنيفها صحيحًا، ثم أدّى التعديل إلى تصنيفها ضارة. هذه حالة إنذار كاذب، وليست برمجية ضارة أفلتت من الكشف.'],
    ['Experimental detector — research only','كاشف تجريبي — للبحث فقط'],
    ['Frozen evaluation model','frozen model للتقييم'],
    ['Full operating-validation accuracy: ','الدقة على مجموعة التحقق التشغيلية الكاملة: '],
    [', below the 93% freeze gate. Small-cohort results below do not replace full validation.','، وهي دون freeze gate البالغة 93%. نتائج cohort الصغيرة لا تحلّ محل التحقق الكامل.'],
    ['A frozen model does not establish that a feature edit is a valid executable modification.','frozen model لا يثبت صلاحية تعديل الخصائص كتعديل لملف تنفيذي.'],
    ['This is a research prototype, not an assurance that a file is safe.','هذا نموذج بحثي، ولا يقدّم ضمانًا لسلامة أي ملف.'],
    ['Model readiness details','تفاصيل جاهزية النموذج'],
    ['ONE MEASURED CASE','حالة واحدة مقاسة'],
    ['Known dataset label: ','التصنيف المرجعي في البيانات: '],
    ['This reference label is how we judge correctness; it is not a model guess.','نستخدم التصنيف المرجعي للحكم على صحة القرار؛ فهو ليس توقّعًا صادرًا عن النموذج.'],
    ['Before attack','قبل الهجوم'],['After attack','بعد الهجوم'],
    ['Malicious','ضار'],['Benign','غير ضار'],
    ['Correct decision','قرار صحيح'],['Incorrect decision','قرار خاطئ'],
    [' against the known label',' مقارنة بالتصنيف المرجعي'],
    ['Malicious-class score','درجة الفئة الضارة'],['Model score for malicious: ','درجة النموذج للفئة الضارة: '],
    ['The score is not file safety or attack success rate. The classification threshold is 50%.','ليست الدرجة احتمال سلامة الملف ولا ASR. عتبة التصنيف في هذه الحالة هي 50%.'],
    ['What happened?','تفسير النتيجة'],['What changed?','ما الذي تغيّر؟'],
    ['Recorded file-size value','قيمة حجم الملف المسجّلة'],
    ['Feature','الخاصية'],['Before','قبل'],['After ≈','بعد ≈'],
    ['No coordinates changed above the 10⁻⁶ measurement tolerance.','لم يتجاوز التغيّر في أي خاصية حدّ سماحية القياس البالغ 10⁻⁶.'],
    ['Raw values after the change are approximate inverse transforms, rounded for integer features. These are feature edits, not edits to an actual file.','القيم الخام بعد التعديل تقديرات ناتجة عن عكس التحويل، مع تقريب الخصائص الصحيحة. هذه تعديلات للخصائص، لا لملف فعلي.'],
    ['Norms use standardized model coordinates; ε is not a percentage.','تُحسب norm في إحداثيات النموذج المعيارية؛ ولا تمثّل ε نسبة مئوية.'],
    ['Planned · Sprint 9–12','مخطّط · المراحل 9–12'],
    ['What happens after hardening?','ما الخطوة التالية لتعزيز المتانة؟'],
    ['We will add measured hardened-model comparisons and re-attack that model. Defense results are not available yet; no improvement is assumed.','نخطّط لمقارنة نماذج عُزّزت متانتها ثم إعادة مهاجمتها. لا تتوافر نتائج دفاعية بعد، ولا نفترض تحسّنًا مسبقًا.'],
    ['The first available case of each outcome is deliberately selected for explanation, not as an independent statistical sample.','نختار أول حالة متاحة من كل نوع نتيجة لغرض الشرح، لا بوصفها عينة إحصائية مستقلة.'],
    ['evaluated samples','عينة مُقيّمة'],['correct decisions: before → after','القرارات الصحيحة: قبل ← بعد'],
    ['induced errors / initially correct · ','الأخطاء المستحدثة / القرارات الصحيحة أصلًا · '],
    ['ASR includes errors induced in either class, not only missed malicious samples.','يشمل ASR الأخطاء المستحدثة في الفئتين، لا حالات إغفال العينات الضارة وحدها.'],
    ['Case provenance and comparison limits','مصدر الحالة وحدود المقارنة'],
    ['Same recorded model, cohort and policy. The row is a dataset split reference, not an uploaded filename. No executables or complete feature arrays reach the browser.','تستخدم المقارنة النموذج وcohort وسياسة القيود نفسها. يشير رقم الصف إلى موضع في تقسيم البيانات، لا إلى اسم ملف مرفوع. ولا تُرسل ملفات تنفيذية أو مصفوفات خصائص كاملة إلى المتصفح.'],
    ['Larger evaluations and an accepted baseline are needed before generalizing. Aggregate-only historical reports remain available in Attack comparison.','يتطلّب التعميم تقييمات أوسع وخط أساس مقبولًا. وتبقى التقارير التاريخية ذات النتائج المجمّعة متاحة في مقارنة الهجمات.'],
    ['No individual case is recorded for this configuration. Open Attack comparison for aggregate results.','لا توجد حالة فردية مسجّلة لهذا الإعداد. راجع مقارنة الهجمات للاطلاع على النتائج المجمّعة.'],
    ['No measured individual cases are available yet. Open Attack comparison for aggregate results; we will not invent a story from aggregate numbers.','لا تتوافر حالات فردية مقاسة بعد. راجع مقارنة الهجمات للنتائج المجمّعة؛ ولا نستنتج حالة فردية من إحصاءات عامة.'],
    ['Experiments with measured individual cases: ','تجارب تتضمّن حالات فردية مقاسة: '],
    ['Invalid reports excluded: ','التقارير غير الصالحة المستبعدة: '],
    [' invalid reports.',' تقرير غير صالح.'],
    [' The list is bounded; not all reports are shown.',' القائمة محدودة؛ ولا تعرض جميع التقارير.'],
    ['Could not load results. Check that the API is running, then ','تعذّر تحميل النتائج. تحقّق من تشغيل واجهة البحث ثم '],['Retry','أعد المحاولة'],
    ['Attack results','نتائج الهجمات'],['Overview','نظرة عامة'],['Model performance','أداء النماذج'],
    ['Dataset explorer','استكشاف البيانات'],['Methodology','المنهجية'],['Tooling demo','عرض أدوات الاختبار'],
    ['WORKSPACE','مسارات البحث'],['Workspace','البحث'],['RESEARCH ENVIRONMENT','بيئة بحثية'],
    ['Build. Challenge. Defend.','تدريب، واختبار، ودفاع مخطّط.'],
    ['↻ Refresh results','↻ تحديث النتائج'],['↻ Refresh data','↻ تحديث البيانات'],
    ['How does the baseline hold up?','كيف يتأثّر النموذج بالهجمات؟'],
    ['Measured clean and attacked results, with the conditions behind every number.','نتائج مقاسة قبل الهجوم وبعده، مع توضيح شروط كل قياس.'],
    ['Loading completed experiments…','جارٍ تحميل التجارب المكتملة…'],['Experiment snapshot','سجلّ التجربة'],
    ['All compatible attacks','جميع الهجمات المتوافقة'],['Norm','Norm'],['Attack','الهجوم'],
    ['One exact model, dataset, split, row subset and policy per snapshot. Norms stay separate.','يرتبط كل سجلّ بنموذج وبيانات وتقسيم وعينات وسياسة قيود محدّدة، وتُعرض كل norm على حدة.'],
    ['Comparison identity','هوية المقارنة'],['Model, cohort and policy provenance','مصدر النموذج وcohort وسياسة القيود'],
    ['CLEAN ACCURACY','الدقة قبل الهجوم'],['EVALUATED ROWS','الصفوف المُقيّمة'],['ASR DENOMINATOR','مقام ASR'],['MAXIMUM MEASURED ASR','أعلى ASR مقاس'],
    ['Identical rows for every displayed result','الصفوف نفسها لجميع النتائج المعروضة'],['Originally correct · both classes','القرارات الصحيحة أصلًا · الفئتان'],
    ['Accuracy versus epsilon','الدقة مقابل مقدار التعديل ε'],
    ['Clean versus attacked · measured results','قبل الهجوم وبعده · نتائج مقاسة'],
    ['Back to dashboard','العودة إلى الصفحة الرئيسية'],
    ['Resilience starts with visibility.','المتانة تبدأ بفهم الأدلة.'],
    ['A clear view of your data, baseline models and measured results.','عرض للبيانات والنماذج الأساسية والنتائج المقاسة، مع حدود تفسيرها.'],
    ['Every model. Every metric.','مقارنة النماذج والمقاييس.'],
    ['Compare measured performance on the same validation data.','قارن الأداء المقاس على بيانات التحقق نفسها.'],
    ['Know the data behind the decision.','افهم البيانات التي يستند إليها القرار.'],
    ['Explore dataset composition, quality and reproducible provenance.','استكشف تركيب البيانات وجودتها ومصدرها الموثّق.'],
    ['Built on evidence.','بحث قائم على الأدلة.'],
    ['Understand the threat model, feature constraints and research limitations.','تعرّف إلى نموذج التهديد وقيود الخصائص وحدود البحث.'],
    ['A separate proving ground.','اختبار مستقل لأدوات البحث.'],
    ['MNIST demonstrates the attack tooling; it is separate from malware results.','تعرض MNIST عمل أدوات الهجوم؛ ونتائجها مستقلة عن نتائج كشف البرمجيات الضارة.'],
    ['Research API online','واجهة البحث متصلة'],['Connecting','جارٍ الاتصال'],['API unavailable','واجهة البحث غير متاحة'],
    ['Loading research results…','جارٍ تحميل نتائج البحث…'],['Unavailable','غير متاح'],['Pending','قيد الانتظار'],
    ['Dataset','مجموعة البيانات'],['Datasets','مجموعات البيانات'],['Inspect model','استعرض النموذج'],['Document','المستند'],
    ['Known limitations','القيود المعروفة'],['Research notes','وثائق البحث'],
    ['CLASS','الفئة'],['RECORDS','السجلات'],['MODEL','النموذج'],['ACCURACY','الدقة'],['PRECISION','إحكام التنبؤ بالفئة الضارة'],['RECALL','استدعاء الفئة الضارة'],['F1 SCORE','درجة F1'],
    ['Source class composition','توزيع فئات المصدر'],['Recorded data splits','تقسيمات البيانات المسجّلة'],['Provenance and limitations','المصدر والقيود'],
    ['Interpretation','التفسير'],['Confusion matrix','مصفوفة الالتباس'],
    ['Reproducibility & training history','قابلية إعادة التجربة وسجلّ التدريب'],['Full stored experiment and reproducibility data','السجلّ الكامل للتجربة وبيانات إعادة تنفيذها'],
    ['ATTACK / PARAMETERS','الهجوم / المعاملات'],['CLEAN','قبل الهجوم'],['ATTACKED','بعد الهجوم'],['ASR / COUNTS','ASR / الأعداد'],
    ['MEAN L0 / L2 / L∞','متوسط L0 / L2 / L∞'],['PROVENANCE / CROSS-CHECK','المصدر / التحقق المستقل'],
    ['No completed results match these filters. Choose another attack or norm.','لا توجد نتائج مكتملة تطابق هذه الخيارات. اختر هجومًا أو norm آخر.'],
    ['No epsilon curve applies.','لا ينطبق منحنى ε هنا.'],['CleverHans: Not run','CleverHans: لم يُنفّذ'],
    ['MODELS & DATA / SPRINT 05','النماذج والبيانات / نتائج التطوير'],
    ['ADVERSARIAL EVALUATION / SPRINT 05','adversarial evaluation / نتائج استكشافية'],
    ['TRANSFER EVALUATION / SPRINT 06','تقييم transfer / نتائج استكشافية'],
    ['SOURCE SAMPLES','عينات المصدر'],['BASELINE MODELS','النماذج الأساسية'],['BEST VALIDATION ACCURACY','أعلى دقة تحقق'],['VALIDATION SAMPLES','عينات التحقق'],
    ['Measured development runs','تجارب تطوير مقاسة'],['Held-out test remains untouched','لم تُستخدم بيانات الاختبار المحجوزة'],
    ['Baseline performance','أداء النماذج الأساسية'],['VALIDATION ONLY','نتائج تحقق فقط'],
    ['Dataset splits','تقسيمات البيانات'],['Model comparison','مقارنة النماذج'],['LIVE ARTIFACTS','سجلّات بحثية متاحة'],
    ['Training split','تقسيم التدريب'],['Validation split','تقسيم التحقق'],['Official test split','تقسيم الاختبار الرسمي'],
    ['Available labeled records','السجلات المصنّفة المتاحة'],['Time-based split','تقسيم زمني'],['Reserved for gated evaluation','محجوز للتقييم المشروط بالاعتماد'],
    [' training rows used in this comparison.',' صف تدريب مستخدم في هذه المقارنة.'],[' Results are developmental.',' النتائج مخصّصة للتطوير.'],
    ['Research boundaries','حدود البحث'],
    ['Historical Sprint 3 development comparison; these uncalibrated scores do not describe the Sprint 4 candidate. Open Attack comparison for Sprint 5 results. Executable scanning and production deployment remain outside the current implementation.','هذه مقارنة تطوير تاريخية من المرحلة 3؛ درجاتها غير المعايرة لا تصف النموذج المرشّح في المرحلة 4. راجع مقارنة الهجمات لنتائج المرحلة 5. فحص الملفات التنفيذية والنشر الإنتاجي خارج نطاق التنفيذ الحالي.'],
    ['BEST ACCURACY','أعلى دقة'],['FALSE POSITIVES','معدّل الإنذارات الكاذبة'],['Accuracy','الدقة'],['F1 score','درجة F1'],
    ['Experiment batch','دفعة التجارب'],['Same dataset · same rows · same split','البيانات نفسها · الصفوف نفسها · التقسيم نفسه'],
    ['Validation metrics by model','مقاييس التحقق حسب النموذج'],['Performance comparison','مقارنة الأداء'],['INDIVIDUAL METRICS','المقاييس التفصيلية'],['Run details','تفاصيل التجربة'],
    ['Training rows','صفوف التدريب'],['Validation rows','صفوف التحقق'],['Seed','بذرة العشوائية'],['Training subset','مجموعة تدريب جزئية'],['Full training split','تقسيم التدريب الكامل'],
    ['validation only','تحقق فقط'],['test not evaluated','لم يُقيّم الاختبار'],['test evaluated','قُيّم الاختبار'],
    ['Actual class → predicted class · exact counts','الفئة الحقيقية ← الفئة المتوقّعة · أعداد فعلية'],
    ['Benign → benign','غير ضار ← غير ضار'],['Benign → malicious (false alarm)','غير ضار ← ضار (إنذار كاذب)'],['Malicious → benign (missed)','ضار ← غير ضار (إغفال)'],['Malicious → malicious','ضار ← ضار'],
    ['Scores are model estimates, not guarantees that a file is safe. A decision margin is used for Linear SVM.','الدرجات تقديرات للنموذج، وليست ضمانًا لسلامة الملف. يستخدم Linear SVM هامش قرار.'],
    ['SOURCE RECORDS','سجلات المصدر'],['FEATURE DIMENSIONS','أبعاد الخصائص'],['PROCESSING SCOPE','نطاق المعالجة'],['LOCAL VERIFICATION','التحقق المحلي'],
    ['Recorded EDA report','تقرير التحليل الاستكشافي المسجّل'],['Numeric feature representation','تمثيل رقمي للخصائص'],['Recorded manifest','بيان بيانات مسجّل'],['Not checked','لم يُتحقق منه'],['Use the preprocessing CLI','استخدم أداة المعالجة المسبقة عبر سطر الأوامر'],
    ['Time-based validation. Official test set preserved.','تحقق زمني؛ مع الحفاظ على مجموعة الاختبار الرسمية.'],['Binary-stratified random split; rare classes may be absent.','تقسيم عشوائي طبقي للفئتين؛ قد تغيب الفئات النادرة.'],
    ['These are recorded dataset reports, not a fresh verification of local arrays.','هذه تقارير بيانات مسجّلة، وليست تحققًا جديدًا من المصفوفات المحلية.'],['Manifest, cleaning and feature metadata','بيان البيانات والتنظيف ووصف الخصائص'],['Unlabeled','غير مصنّف'],['Subset','جزئي'],['Full','كامل'],
    ['EVIDENCE & LIMITATIONS','الأدلة والقيود'],['MNIST environment check only. These results do not measure EMBER malware robustness.','هذا فحص لبيئة الأدوات على MNIST فقط؛ ولا تقيس نتائجه متانة كشف البرمجيات الضارة على EMBER.'],
    ['CLEAN MNIST ACCURACY','دقة MNIST قبل الهجوم'],['Recorded Sprint 1 tooling run','تجربة أدوات مسجّلة من المرحلة 1'],['SEED','بذرة العشوائية'],['Reproducible run configuration','إعدادات قابلة لإعادة التنفيذ'],['TRAINING EPOCHS','دورات التدريب'],['MNIST demonstration','عرض MNIST'],['DOMAIN','المجال'],['Separate from malware detection','مستقل عن كشف البرمجيات الضارة'],['Attack tooling results','نتائج أدوات الهجوم'],['Recorded accuracy under attack','الدقة المسجّلة تحت الهجوم'],['Loading figure…','جارٍ تحميل الرسم…'],
    ['Frozen baseline · feature prediction (Sprint 4)','frozen baseline · تصنيف الخصائص (المرحلة 4)'],
    ['The comparison tables above retain Sprint 3 validation-only results. For Sprint 4 evaluation and M1 status, open Methodology → sprint4, or load the frozen identity below.','تحتفظ الجداول بنتائج التحقق التاريخية للمرحلة 3. لتقييم المرحلة 4 وحالة بوابة M1، افتح المنهجية ← sprint4، أو حمّل هوية frozen model أدناه.'],
    ['Public EMBER2018 v2 feature rows only. No executable or PCAP uploads. Scores are research estimates, not file-safety guarantees. Prediction remains unavailable until M1 passes.','يُقبل فقط تمثيل الخصائص العام EMBER2018 v2، دون رفع ملفات تنفيذية أو PCAP. الدرجات تقديرات بحثية لا ضمانات لسلامة الملفات. يظل التصنيف غير متاح حتى اجتياز بوابة M1.'],
    ['Prediction access token (not saved)','رمز الوصول إلى التصنيف (لا يُحفظ)'],['Load frozen model identity','تحميل هوية frozen model'],['Feature representation','تمثيل الخصائص'],['Raw EMBER feature values','قيم خصائص EMBER الخام'],["Already signed-log1p standardized with this model's scaler",'قيم محوّلة بـ signed-log1p ومعيارية بمحوّل هذا النموذج'],['Ordered numeric rows as JSON (1–32 rows × 2381 features)','صفوف رقمية مرتّبة بصيغة JSON (1–32 صفًا × 2381 خاصية)'],['Predict features','تصنيف الخصائص'],
    ['No frozen model loaded.','لم يُحمّل frozen model.'],['Load a verified frozen baseline first.','حمّل frozen baseline متحقّقًا منه أولًا.'],
    ['Access denied. Check the prediction token.','رُفض الوصول. تحقّق من رمز التصنيف.'],['Request too large.','حجم الطلب يتجاوز الحدّ المسموح.'],
    ['Invalid rows or schema/preprocessing identity.','الصفوف أو هوية المخطط أو المعالجة المسبقة غير صالحة.'],
    ['Query budget exceeded. Wait one minute.','تجاوزت حدّ الاستعلامات. انتظر دقيقة واحدة.'],
    ['Prediction unavailable: token not configured or M1 baseline not frozen.','التصنيف غير متاح: رمز الوصول غير مضبوط أو خط أساس M1 غير مجمّد.'],
    ['Prediction request failed.','تعذّر إتمام طلب التصنيف.'],
    ['Expected 1–32 finite numeric rows, each with exactly 2381 features.','أدخل 1–32 صفًا من أعداد منتهية، يحتوي كل منها على 2381 خاصية بالضبط.'],
    ['Invalid JSON. Enter an array of numeric rows.','صيغة JSON غير صالحة. أدخل مصفوفة من الصفوف الرقمية.'],
    ['Connection failed or timed out. Please retry.','تعذّر الاتصال أو انتهت مهلته. أعد المحاولة.'],
    ['Loading frozen model identity…','جارٍ تحميل هوية frozen model…'],['Classifying feature rows…','جارٍ تصنيف صفوف الخصائص…'],
    ['[[...2381 numeric values...]]','[[...2381 قيمة رقمية...]]'],
    ['Accuracy:','الدقة:'],['Perturbations:','perturbation:'],['Constraints:','القيود:'],['Cross-check:','التحقق المستقل:'],
    [' correct decisions ÷ all evaluated rows. Clean and attacked scores use the same rows.',' القرارات الصحيحة ÷ جميع الصفوف المُقيّمة. تُستخدم الصفوف نفسها قبل الهجوم وبعده.'],
    [' originally correct decisions made incorrect ÷ originally correct decisions. Both benign and malicious rows are included; this is untargeted error induction, not a malware-only evasion rate. An empty denominator is unavailable.',' القرارات الصحيحة التي أصبحت خاطئة ÷ القرارات الصحيحة أصلًا. يشمل الحساب الفئتين؛ وهو قياس لاستحداث أخطاء غير موجّهة، لا لتجاوز كشف البرمجيات الضارة وحدها. النتيجة غير متاحة عند خلوّ المقام.'],
    [' mean L0 (changed coordinates above 10⁻⁶), L2 and L∞ across all evaluated rows, in signed-log1p standardized model coordinates. Epsilon is not a percentage or a raw byte budget.',' متوسط L0 (الخصائص المتغيّرة بأكثر من 10⁻⁶) وL2 وL∞ لجميع الصفوف، في إحداثيات النموذج المعيارية بعد signed-log1p. لا تمثّل ε نسبة مئوية ولا حدًا لعدد البايتات الخام.'],
    [' bounds, immutable masks and integer counts are feature-space approximations. They do not establish a valid executable. CW-L2 is projected after generation and is not a constrained optimum.',' الحدود والخصائص الثابتة والأعداد الصحيحة تقريبات في feature space، ولا تثبت صلاحية ملف تنفيذي. تُطبّق القيود على CW-L2 بعد التوليد؛ وليست النتيجة حلًا أمثل مقيّدًا.'],
    [' CleverHans is an independent implementation; matching metrics alone do not prove equivalent attacks. Missing checks remain “Not run”. No experiments are executed from this page.',' CleverHans تنفيذ مستقل؛ ولا يثبت تطابق المقاييس تكافؤ الهجمات. تبقى الاختبارات الغائبة موسومة «لم يُنفّذ». ولا تُشغّل هذه الصفحة تجارب.'],
    ['White-box and black-box evidence','أدلة white-box وblack-box'],
    ['Recorded results only. No training, live attacks or uploads.','نتائج مسجّلة فقط، دون تدريب أو هجمات مباشرة أو رفع ملفات.'],
    ['Four realism requirements','أربعة متطلبات للواقعية'],
    ['Scalar feature feasibility','صلاحية قيم الخصائص الفردية'],
    ['Policy projection checks numeric bounds, integer values and immutable coordinates only.','يتحقق تطبيق سياسة القيود من الحدود الرقمية والقيم الصحيحة والخصائص الثابتة فقط.'],
    ['Coupled structural consistency','الاتساق البنيوي بين الخصائص المترابطة'],
    ['Not established. Derived features are not recomputed together.','غير مُثبت. لا يُعاد حساب الخصائص المشتقّة بصورة مترابطة.'],
    ['Executable realizability','إمكان تحقيق التعديل في ملف تنفيذي'],
    ['Not established. No authorized isolated-lab PE demonstration.','غير مُثبت. لم تُجرَ تجربة مصرّح بها على ملف تنفيذي محمول (PE) في مختبر معزول.'],
    ['Preserved behavior','الحفاظ على السلوك'],
    ['Not established. No executable was modified or run.','غير مُثبت. لم يُعدّل أو يُشغّل أي ملف تنفيذي.'],
    ['Owner authorization is not technical Security review. A feature edit proves none of the other three properties.','إذن المالك لا يعادل المراجعة الأمنية التقنية. تعديل خاصية لا يثبت أيًا من الخصائص الثلاث الأخرى.'],
    ['Proposed threat mappings','ربط مقترح بتصنيفات التهديد'],
    ['Technical Security review pending. Mappings describe methods and intent, not successful real-world compromise.','المراجعة الأمنية التقنية قيد الانتظار. يصف الربط الأساليب والغايات، ولا يثبت اختراقًا ناجحًا في الواقع.'],
    ['Scope and missing evidence','النطاق والأدلة غير المتاحة'],
    ['HopSkipJump and ZOO: not implemented, not run. CICIDS: inactive; no trained IDS evidence. Problem-space lab: not authorized, not run. M1 and frozen-benchmark acceptance remain separate.','لم يُنفّذ أو يُشغّل HopSkipJump وZOO. مسار CICIDS غير نشط، ولا توجد أدلة على IDS مدرّب. مختبر الملفات الفعلية غير مصرّح به ولم يُشغّل. يظل قبول M1 وfrozen benchmark مسألتين منفصلتين.'],
    ['Transfer ASR uses target-clean-correct rows, not source successes. Conditional transfer additionally requires both models initially correct and source attack success. Preexisting errors are never attack successes.','يعتمد قياس ASR في transfer على الصفوف التي صنّفها النموذج الهدف صحيحًا قبل الهجوم، لا نجاحات المصدر. ويشترط transfer المشروط صحة قرار النموذجين أولًا ونجاح الهجوم على المصدر. لا تُحتسب الأخطاء السابقة نجاحًا للهجوم.'],
    ['Malware evasion counts initially detected malicious rows made benign. False-positive induction counts initially correct benign rows made malicious. Empty denominators are unavailable, not zero.','يحسب تجاوز الكشف العينات الضارة المكتشفة أصلًا التي أصبحت غير ضارة في تصنيف النموذج. ويحسب استحداث الإنذارات الكاذبة العينات غير الضارة التي تحوّل تصنيفها الصحيح إلى ضار. المقام الخالي يعني نتيجة غير متاحة، لا صفرًا.'],
    ['Shared training data and preprocessing are attacker knowledge assumptions, not a strict unknown-data black-box scenario.','اشتراك بيانات التدريب والمعالجة المسبقة افتراض عن معرفة المهاجم، وليس سيناريو black-box ببيانات مجهولة تمامًا.'],
    ['Pending / unavailable','قيد الانتظار / غير متاح'],
    ['White-box and black-box results','نتائج white-box وblack-box'],
    ['Attacker knowledge and provenance','معرفة المهاجم ومصدر الأدلة'],
    ['Source gradients only; no target feedback during crafting. Public true labels. All rows retained, with no target-based filtering.','تُستخدم تدرّجات المصدر فقط، دون تغذية راجعة من الهدف أثناء التوليد. التصنيفات المرجعية عامة، وتُحتفظ بجميع الصفوف دون ترشيح وفق نتائج الهدف.'],
    ['White-box target gradients. Transfer has not been measured in this snapshot.','تُستخدم تدرّجات الهدف ضمن إعداد white-box. لم يُقَس transfer في هذا السجلّ.'],
    ['Correct / all rows; ASR numerator / clean-correct denominator. Class-specific rates use class-specific clean-correct denominators.','الصحيح / جميع الصفوف؛ وبسط ASR / مقام القرارات الصحيحة قبل الهجوم. تستخدم المعدّلات الخاصة بكل فئة مقام قراراتها الصحيحة أصلًا.'],
    ['Knowledge','معرفة المهاجم'],['Model','النموذج'],['Attacked correct','الصحيح بعد الهجوم'],
    ['Malware evasion','تجاوز كشف البرمجيات الضارة'],['False-positive induction','استحداث إنذارات كاذبة'],['Preexisting errors','أخطاء سابقة للهجوم'],
    ['Surrogate white-box','surrogate · white-box'],['Black-box transfer','black-box · transfer'],['White-box','white-box'],['Source','المصدر'],['Target','الهدف'],
    ['Conditional transfer','transfer مشروط'],['Transferred sample digest','بصمة عينات transfer'],
    ['Deliberately selected case studies are available in the AI journey when recorded.','تُعرض الحالات المختارة عمدًا للشرح في رحلة التجربة عند تسجيلها.'],
    ['Transfer results pending. Recorded white-box results are not black-box evidence.','نتائج transfer قيد الانتظار. لا تُعدّ نتائج white-box دليلًا على black-box.'],
    ['No measured results available. Missing evidence is not a zero success rate.','لا تتوافر نتائج مقاسة. غياب الأدلة لا يعني أن ASR صفر.'],
    ['Threat mappings unavailable.','ربط التهديدات غير متاح.'],
    ['OWASP ML07 transfer learning is not adversarial-example transfer. ATLAS evasion intent does not establish executable evasion.','منهج transfer learning في OWASP ML07 ليس transfer لـ adversarial examples. وغاية تجاوز الكشف في ATLAS لا تثبت تحقيقها بملف تنفيذي.'],
    ['Could not load results. Use refresh to retry.','تعذّر تحميل النتائج. استخدم التحديث لإعادة المحاولة.'],
    ['Completed snapshots: ','سجلّات التجارب المكتملة: '],
    ['Feature-space only','feature space فقط'],
    ['Scalar constraints only. Coupled consistency, executable realizability and preserved behavior are not established.','قيود على الخصائص الفردية فقط. لم يُثبت الاتساق المترابط أو إمكان تحقيق التعديل في ملف تنفيذي أو الحفاظ على السلوك.'],
    ['Source and target decisions','قرارات المصدر والهدف'],['Known label: ','التصنيف المرجعي: '],
    ['. Scores are not file-safety guarantees.','. الدرجات ليست ضمانًا لسلامة الملفات.'],
    ['White-box target gradients. Transfer has not been measured for this case.','تُستخدم تدرّجات الهدف ضمن إعداد white-box. لم يُقَس transfer لهذه الحالة.'],
    [' Constraint review: ',' مراجعة القيود: '],['Constraint review: ','مراجعة القيود: '],
    ['Problem-space validity: not established.','صلاحية التعديل في ملف فعلي: غير مُثبتة.'],
    ['Development model — not frozen','نموذج تطوير — غير مجمّد'],
    ['Experiment scope and readiness','نطاق التجربة وجاهزيتها'],
    ['This exploratory experiment does not complete M1 or enable prediction.','لا تستكمل هذه التجربة الاستكشافية بوابة M1 ولا تتيح التصنيف.'],
    ['Official test evaluated for this model: ','تقييم الاختبار الرسمي لهذا النموذج: '],
    ['. Attack cohort: ','. cohort الهجوم: '],
    ['Feature-space experiment · Technical Security review: ','تجربة في feature space · المراجعة الأمنية التقنية: '],
    [' · Problem-space validation: unavailable.',' · التحقق في ملف فعلي: غير متاح.'],
    ['Asserted by the named local reviewer','وفق إفادة المراجع المحلي المسمّى'],
    ['CW-L2 uses optimization parameters and L2 distortion.','يستخدم CW-L2 معاملات optimization ومقدار التعديل L2.'],
    ['Dashed line: clean accuracy. Exact values and counts appear below.','الخط المتقطّع: الدقة قبل الهجوم. ترد القيم والأعداد الدقيقة أدناه.'],
    ['ε · standardized model coordinates','ε · إحداثيات النموذج المعيارية'],
    ['Scrollable accuracy chart','رسم الدقة القابل للتمرير'],
    ['Accuracy versus epsilon; exact values in the results table','الدقة مقابل ε؛ القيم الدقيقة في جدول النتائج'],
    ['Scroll the chart horizontally for all epsilon values. Exact values are in the table below.','مرّر الرسم أفقيًا لاستعراض جميع قيم ε. القيم الدقيقة في الجدول أدناه.'],
    ['Grouped comparison of accuracy, F1 and AUC; exact values in the model table.','مقارنة الدقة وF1 والمساحة تحت المنحنى؛ القيم الدقيقة في جدول النماذج.'],
    ['Scrollable evidence table','جدول أدلة قابل للتمرير'],
    ['Model bundle SHA-256','بصمة حزمة النموذج SHA-256'],['Exact row indices SHA-256','بصمة فهارس الصفوف SHA-256'],['Constraint policy SHA-256','بصمة سياسة القيود SHA-256'],
    ['Model SHA-256','بصمة النموذج SHA-256'],['Cohort SHA-256','بصمة cohort SHA-256'],['Policy SHA-256','بصمة السياسة SHA-256'],
    ['Target SHA-256','بصمة الهدف SHA-256'],['Source SHA-256','بصمة المصدر SHA-256'],['Dataset manifest SHA-256','بصمة بيان البيانات SHA-256'],['Preprocessing SHA-256','بصمة المعالجة المسبقة SHA-256'],
    ['Constraint status: ','حالة القيود: '],[' · reviewer: ',' · المراجع: '],[' · problem-space validation: unavailable.',' · التحقق في ملف فعلي: غير متاح.'],
    ['No completed baseline runs. Process EMBER and run the training command, then refresh.','لا توجد تجارب أساسية مكتملة. يلزم إعداد EMBER وتنفيذ أمر التدريب خارج الموقع، ثم تحديث العرض.'],
    ['No completed runs available.','لا تتوافر تجارب مكتملة.'],['No completed results','لا توجد نتائج مكتملة'],['No comparison run selected.','لم تُحدّد تجربة للمقارنة.'],
    ['Unable to load this page. Check the research API and use Refresh data to retry. Your files have not been changed.','تعذّر تحميل الصفحة. تحقّق من واجهة البحث ثم استخدم تحديث البيانات. لم تُعدّل ملفاتك.'],
    ['Connecting to research API…','جارٍ الاتصال بواجهة البحث…'],
    ['Recorded MNIST accuracy under attack','دقة MNIST المسجّلة تحت الهجوم'],
    ['Results unavailable. Check the API and refresh. No cached scores are being shown.','النتائج غير متاحة. تحقّق من واجهة البحث ثم حدّث العرض. لا تُعرض درجات مخزّنة مؤقتًا.'],
    ['Results pending: ','النتائج قيد الانتظار: '],
    ['Requires frozen M1 baseline and explicit feature-space policy; technical review status is reported separately','يلزم اعتماد frozen baseline لـ M1 وسياسة صريحة في feature space؛ وتُعرض حالة المراجعة التقنية بصورة مستقلة'],
    ['Optional isolated CleverHans check not requested','لم يُطلب التحقق الاختياري المعزول باستخدام CleverHans'],
    ['No measured EMBER attack scores are available.','لا تتوافر درجات مقاسة لهجمات EMBER.'],
    ['Completed experiment snapshots: ','سجلّات التجارب المكتملة: '],
    ['Configurations shown: ','الإعدادات المعروضة: '],
    [' Result listing limited; some reports are omitted.',' قائمة النتائج محدودة؛ بعض التقارير غير معروضة.'],
    ['Invalid batches excluded: ','الدفعات غير الصالحة المستبعدة: '],['Only the latest 100 batches are shown.','تُعرض أحدث 100 دفعة فقط.'],
    ['ARSM / Attack comparison','ARSM / مقارنة الهجمات'],
    ['ARSM / Threat context and transfer','ARSM / سياق التهديد وtransfer'],
    ['ARSM / Models and data','ARSM / النماذج والبيانات'],
    ['ARSM / Adversarial-Resilient Security Models','ARSM / نماذج أمنية تقاوم adversarial attacks'],
    ['L∞ · epsilon sweep','L∞ · تدرّج قيم ε'],
    ['Linear SVM','آلة المتجهات الداعمة الخطية (Linear SVM)'],
    ['Logistic Regression','الانحدار اللوجستي'],['Random Forest','الغابة العشوائية'],['Neural Network · MLP','شبكة عصبية متعدّدة الطبقات (MLP)'],
    ['Logistic','لوجستي'],['Forest','غابة عشوائية'],
    ['feasibility','دراسة الجدوى'],['threat-model','نموذج التهديد'],['ember-literature','أدبيات EMBER'],['cicids-literature','أدبيات CICIDS'],
    ['sprint1','المرحلة 1'],['sprint2','المرحلة 2'],['sprint4','المرحلة 4'],
    ['train','التدريب'],['val','التحقق'],['test','الاختبار'],
    ['yes','نعم'],['no','لا'],['correct','صحيح'],['accuracy','الدقة'],
    ['iterations','تكرار'],['searches','عملية بحث'],['step','خطوة'],['rows','صف'],['row','صف'],['samples','عينة'],['seed','بذرة'],['threshold','عتبة'],['configurations','إعداد'],
    ['Updated ','آخر تحديث '],['Generated ','تاريخ الإنشاء '],
    ['prediction agreement','اتفاق التنبؤات'],['mean candidate L2 difference','متوسط فرق L2 بين المرشّحات'],
    ['Interpretation guide: accuracy is the share of correct decisions; precision and recall describe the malicious class. F1 balances precision and recall; ROC-AUC measures ranking across thresholds.','دليل المقاييس: الدقة هي نسبة القرارات الصحيحة؛ ويصف الإحكام والاستدعاء أداء الفئة الضارة. توازن F1 بينهما، وتقيس ROC-AUC جودة ترتيب العينات عبر العتبات.'],
    ['Research maturity','حالة البحث'],
    ['Measured: exploratory feature-space attacks. Pending: M1 acceptance, frozen benchmark and transfer measurements. Planned: defenses.','المقاس: هجمات استكشافية في feature space. قيد الانتظار: قبول M1 وfrozen benchmark وقياسات transfer. المخطّط: الدفاعات.'],
    ['Attack success rate (ASR)','ASR'],
    [' on ',' على '],
    [' selected validation rows and cannot satisfy the 93% freeze gate.',' صف تحقق مختارًا، ولا تستوفي freeze gate البالغة 93%.'],
    ['. Charts use ','. تستخدم الرسوم '],
    ['Owner-authorized measured case studies for AI journey; operating validation only, baseline and SS acceptance remain pending','حالات مقاسة لشرح التجربة بإذن المالك؛ تقتصر على التحقق التشغيلي، مع بقاء قبول خط الأساس والمراجعة الأمنية قيد الانتظار'],
    ['Bounded file-size scalar sensitivity probe only. Increase raw general.size by at most 64 KiB while freezing every other coordinate. No bytes are changed and coupled statistics are not recomputed. This is not a realizable append operation or SS-approved feasibility claim.','اختبار محدود لحساسية خاصية الحجم فقط: زيادة general.size الخام بما لا يتجاوز 64 KiB مع تثبيت سائر الخصائص. لا تُعدّل بايتات ولا يُعاد حساب الإحصاءات المترابطة. ليس هذا تنفيذًا لإلحاق بيانات بملف، ولا ادعاء صلاحية معتمدًا أمنيًا.'],
    ['Project owner authorization in chat, 2026-11-14; no SS technical validation claimed','إذن مالك المشروع بتاريخ 2026-11-14؛ دون ادعاء تحقق أمني تقني'],
    ['pending','قيد الانتظار'],['completed','مكتمل'],['not_run','لم يُنفّذ'],
    ['owner_authorized_feature_space','feature space بإذن المالك'],
    ['reviewed_feature_space','feature space خضع لمراجعة محلية'],
    ['development_candidate_not_frozen','مرشّح تطوير غير مجمّد'],['frozen_baseline','frozen baseline'],
    ['operating_validation','التحقق التشغيلي'],
    ['each_step','تطبيق القيود بعد كل خطوة'],['after_generation','تطبيق القيود بعد التوليد'],
    ['كل خوارزمية بتستخدم تدرّجات الموديل المستهدف علشان تعدّل مدخلات التصنيف.','تستخدم كل خوارزمية تدرّجات النموذج الهدف لتعديل مدخلات التصنيف.'],
    ['بنولّد التعديل على موديل بديل مختلف، وبنختبر نفس المدخلات على الهدف من غير أي رد منه أثناء التوليد.','يُولّد التعديل باستخدام surrogate مختلف، ثم تُختبر المدخلات نفسها على الهدف دون تغذية راجعة منه أثناء التوليد.'],
  ];
  const escapeRegex = s => s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  const converters = new Map();
  function translate(text, language) {
    if (!converters.has(language)) {
      const from = language === 'ar' ? 0 : 1, to = 1-from, map = new Map();
      copy.forEach(pair => { if (!map.has(pair[from])) map.set(pair[from],pair[to]); });
      const patterns = [...map.keys()].sort((a,b)=>b.length-a.length).map(key =>
        `${/^[A-Za-z0-9]/.test(key) ? '(?<![A-Za-z0-9_])' : ''}${escapeRegex(key)}${/[A-Za-z0-9]$/.test(key) ? '(?![A-Za-z0-9_-])' : ''}`);
      converters.set(language,{map,pattern:new RegExp(patterns.join('|'),'g')});
    }
    const {map,pattern} = converters.get(language);
    return text.replace(pattern, match => map.get(match));
  }
  // Keep formatted numbers in one directional run, and group multi-word English
  // scientific terms so bidi ordering cannot separate or reverse their words.
  const latinPhrases = [
    'adversarial evaluation',
    'adversarial examples',
    'adversarial attacks',
    'attack success rate',
    'adversarial example',
    'adversarial attack',
    'adversarial tests',
    'frozen benchmark',
    'frozen baseline',
    'frozen model',
    'feature space',
    'freeze gate',
    'transfer learning',
  ];
  const latinRun = new RegExp(
    `(${latinPhrases.map(escapeRegex).join('|')})|([A-Za-z0-9](?:[A-Za-z0-9_.,:/+%∞⁻⁶–-]*[A-Za-z0-9%∞⁻⁶])?)`,
    'gi'
  );
  const isolate = text =>
    text.replace(latinRun, (_, phrase, token) => `\u2066${phrase || token}\u2069`);
  if (typeof module !== 'undefined') module.exports = {translate, isolate, copy};
  if (typeof document === 'undefined') return;
  let language = 'en';
  try { if (localStorage.getItem('arsm-language') === 'ar') language = 'ar'; } catch (_) { /* Session-only choice. */ }
  const originals = new WeakMap(), attributeOriginals = new WeakMap();
  const originalTitle = document.title;
  const switcher = document.createElement('div');
  switcher.className = 'language-switch';
  switcher.setAttribute('role','group');
  switcher.setAttribute('aria-label','Interface language');
  switcher.innerHTML = '<button type="button" data-language="en" lang="en">English</button><button type="button" data-language="ar" lang="ar">العربية</button>';
  document.querySelector('header').append(switcher);
  const skip = document.createElement('a');
  skip.className = 'skip-link'; skip.href = '#main-content'; skip.textContent = 'Skip to content';
  document.body.prepend(skip);
  const main = document.querySelector('main');
  main.id = 'main-content'; main.tabIndex = -1;
  function apply() {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    document.title = translate(originalTitle,language);
    // Translating an option's label must never change the value sent to the API.
    document.querySelectorAll('option:not([value])').forEach(option => { option.value = option.textContent; });
    // Raw evidence remains in its recorded language; status prose inside <pre>
    // is explicitly opted in. JSON keys/values and identifiers are never rewritten.
    const walker = document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let node;
    while ((node=walker.nextNode())) {
      if (!node.textContent.trim() || node.parentElement.closest('script,style,code,.language-switch,[data-release],[data-evidence],pre:not([data-ui-copy])')) continue;
      let record = originals.get(node);
      if (!record || node.textContent !== record.rendered) record = {original:node.textContent};
      record.rendered = translate(record.original,language);
      // Isolate Latin identifiers, timestamps, counts and ratios inside Arabic.
      // Stored source text and numeric evidence stay unchanged.
      if (language === 'ar' && !node.parentElement.closest('[dir="ltr"],bdi')) {
        record.rendered = isolate(record.rendered);
      }
      originals.set(node,record);
      if (node.textContent !== record.rendered) node.textContent = record.rendered;
    }
    document.querySelectorAll('[aria-label],[title],[placeholder],[alt],meta[name="description"]').forEach(element => {
      const records = attributeOriginals.get(element) || {};
      for (const name of ['aria-label','title','placeholder','alt','content']) {
        if (name === 'content' && !element.matches('meta[name="description"]')) continue;
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
    document.querySelectorAll('.table-wrap').forEach(element => {
      element.tabIndex = 0;
      element.setAttribute('role','region');
      if (!element.hasAttribute('aria-label')) element.setAttribute('aria-label',translate('Scrollable evidence table',language));
      element.querySelectorAll('thead th:not([scope])').forEach(th => th.setAttribute('scope','col'));
      const table = element.querySelector('table');
      if (table && !table.querySelector('caption')) {
        const caption = document.createElement('caption');
        caption.textContent = 'Data table';
        table.prepend(caption);
      }
      if (!element.previousElementSibling?.classList.contains('scroll-hint')) {
        const hint = document.createElement('p');
        hint.className = 'scroll-hint';
        hint.textContent = 'Scroll the table horizontally to view all columns.';
        element.before(hint);
      }
    });
    // Screen readers should retain the source language for unlocalized evidence.
    document.querySelectorAll('code,pre,[data-release],[data-evidence]').forEach(element => {
      if (element.matches('pre[data-ui-copy]')) element.removeAttribute('lang');
      else element.lang = 'en';
    });
    document.querySelectorAll('nav button[data-page]').forEach(button => {
      button.setAttribute('aria-current',button.classList.contains('active') ? 'page' : 'false');
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
  window.ARSM = Object.freeze({translate: text => translate(text,language), localize: apply});
  apply();
})();
