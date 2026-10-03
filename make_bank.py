"""One-off: builds the sample questions.json. Format: skill, level, question, CORRECT, wrong1-3, explanation[, passage]"""
import json
G, V, R = "Grammar", "Vocabulary", "Reading"
T = [
(G,"A1.1","She ___ a teacher.","is","are","am","be","Use 'is' with he/she/it."),
(V,"A1.1","Which word is a fruit?","Apple","Table","Door","Shoe","An apple is a fruit."),
(R,"A1.2","What colour is Sam's dog?","Brown","Black","White","Red","The text says the dog is brown.","Sam is 10. He has a dog. The dog is brown."),
(G,"A1.2","I ___ breakfast at 7 every day.","have","has","having","am have","Use 'have' with I."),
(V,"A1.3","The opposite of 'big' is ___.","small","tall","old","long","Big and small are opposites."),
(R,"A1.3","How does Mona go to work?","By bus","By car","On foot","By train","The text says she goes by bus.","Mona gets up at 6. She goes to work by bus."),
(G,"A2.1","Yesterday I ___ to the market.","went","go","goes","going","Past simple of 'go' is 'went'."),
(V,"A2.1","I'm tired, so I'm going to ___ early tonight.","go to bed","go bed","make bed","sleep bed","'Go to bed' is the fixed phrase."),
(R,"A2.2","When can you NOT visit the library?","On Sunday","On Saturday","On Monday","On Friday afternoon","It is closed on Sundays.","The library opens at 9 a.m. and closes at 6 p.m. on weekdays. On Saturdays it closes at 1 p.m. It is closed on Sundays."),
(G,"A2.2","There isn't ___ milk in the fridge.","any","some","a","many","Use 'any' in negatives with uncountable nouns."),
(V,"A2.3","Can you ___ me your pen? I forgot mine.","lend","borrow","rent","keep","You lend something to someone else."),
(R,"A2.3","Why did Ali wait?","The phone cost too much","He did not need a phone","The shop was closed","He lost his money","It was too expensive.","Ali wanted to buy a new phone, but it was too expensive, so he decided to wait for a sale."),
(G,"B1.1","I have lived here ___ 2015.","since","for","from","during","'Since' goes with a starting point."),
(V,"B1.1","She was ___ because she had worked all night.","exhausted","exhausting","exhaust","exhaustion","'Exhausted' describes how a person feels."),
(R,"B1.2","What problem do some home workers have?","They feel lonely","They travel too much","They earn less","They dislike computers","The text mentions loneliness.","Many people now work from home. This saves travel time, but some workers say they feel lonely and find it hard to separate work from free time."),
(G,"B1.2","If I ___ more time, I would learn French.","had","have","will have","would have","Second conditional: if + past simple."),
(V,"B1.3","I'd like to ___ for the job advertised in the newspaper.","apply","ask","request","demand","We 'apply for' a job."),
(R,"B1.3","How does the writer feel about the hotel?","Satisfied","Disappointed","Angry","Confused","Clean rooms and friendly staff; would return.","Although the hotel was cheap, the rooms were clean and the staff were friendly, so we would stay there again."),
(G,"B2.1","By the time we arrived, the film ___.","had already started","already started","has already started","was already start","Past perfect shows the earlier past action."),
(V,"B2.1","I worked late to ___ the time I lost this morning.","make up for","put up with","come up with","look up to","'Make up for' means compensate."),
(R,"B2.2","What do critics fear about remote learning?","It may increase inequality","Students will learn slowly","Teachers will lose jobs","Internet will become expensive","The gap between students widens.","Critics argue that remote learning widens the gap between students with reliable internet and those without, even though it offers flexibility."),
(G,"B2.2","I wish I ___ harder when I was at school.","had studied","studied","would study","have studied","Wish about the past uses past perfect."),
(V,"B2.3","His ___ remarks offended several colleagues.","tactless","tactful","tacit","tactical","'Tactless' means lacking sensitivity."),
(R,"B2.3","What do the authors warn about?","A link does not prove cause","Sleep has no effect","Memory is unrelated","The study was too long","Correlation is not causation.","The study found a correlation between sleep and memory, but the authors caution that this does not prove sleep causes better recall."),
(G,"C1.1","Not only ___ late, but he also forgot the documents.","did he arrive","he arrived","he did arrive","arrived he","Inversion after 'Not only'."),
(V,"C1.1","The two reports are ___; they say the opposite.","contradictory","complementary","redundant","consistent","Contradictory = in conflict."),
(R,"C1.2","What is implied about the statement?","Friendly tone, nothing concrete offered","The unions got what they wanted","The minister was hostile","It was very long","'Superficially conciliatory' but no concessions.","The minister's statement, while superficially conciliatory, offered no concrete concessions to the unions."),
(G,"C1.2","Had I known about the delay, I ___ earlier.","would have left","would leave","had left","left","Third conditional with inversion."),
(V,"C1.3","The politician's ___ rise to power surprised analysts.","meteoric","mundane","latent","tedious","Meteoric = very fast."),
(R,"C1.3","What does the author claim about the metaphor?","It is central to the author's thinking","It is only decoration","Time is not discussed","The author dislikes metaphor","'Far from being a mere ornament'.","Far from being a mere ornament, the metaphor structures how the author thinks about time."),
(G,"C2.1","Scarcely ___ the room when the alarm went off.","had she entered","she had entered","did she enter","she entered","Inversion after 'Scarcely' + past perfect."),
(V,"C2.1","His argument was specious: plausible but ___.","fundamentally flawed","perfectly sound","highly original","deeply emotional","Specious = seems right but is wrong."),
(R,"C2.2","What is still disputed?","Whether the reforms caused the recovery","Whether a recovery happened","Whether reforms existed","Whether anyone read the reports","The success is undisputed; the cause is contested.","That the reforms succeeded is beyond dispute; what remains contested is whether they were the cause of the recovery or merely coincided with it."),
(G,"C2.2","It is high time the government ___ action.","took","takes","will take","taking","'It's high time' + past simple."),
(V,"C2.3","The CEO's ___ stance on the merger left investors uncertain.","equivocal","resolute","candid","emphatic","Equivocal = deliberately unclear."),
(R,"C2.3","What is the author's real attitude to the committee?","Critical","Admiring","Indifferent","Confused","The praise is meant to expose complacency.","The author's irony is easily missed: the praise she lavishes on the committee is calculated to expose its complacency."),
]
out = []
for n, t in enumerate(T, 1):
    s, l, q, a, w1, w2, w3, e = t[:8]
    out.append(dict(id=f"S{n:03d}", skill=s, level=l, question=q, options=[a, w1, w2, w3], answer=a,
                    explanation=e, passage=t[8] if len(t) > 8 else ""))
json.dump(out, open("questions.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "questions")
