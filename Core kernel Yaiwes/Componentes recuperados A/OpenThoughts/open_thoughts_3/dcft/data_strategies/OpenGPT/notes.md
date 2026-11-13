## Recreating Medical Tasks dataset from OpenGPT

> https://github.com/CogStack/OpenGPT/blob/main/data/medical_tasks_gpt4/prepared_generated_data_for_medical_tasks.csv

## Medical Tasks Prompt

Copied from https://github.com/CogStack/OpenGPT/blob/main/experiments/Prompt%20Creation.ipynb

> You are asked to come up with a set of {quantity} diverse task instructions in the field of medicine and healthcare. These task instructions will be given to a Medical GPT model and we will evaluate the Medical GPT model for completing the instructions.
>
>Here are the requirements:
>1. Try not to repeat the verb for each instruction to maximize diversity.
>2. The language used for the instruction also should be diverse. For example, you should combine questions with imperative instructions.
>3. The type of instructions should be diverse. The list should include diverse kinds of tasks like step-by-step reasoning, multiple-choice-questions, open-ended generation, classification, editing, complex medical questions, simple medical questions, etc.
>4. A GPT language model should be able to complete the instruction. For example, do not ask the assistant to create any visual or audio output. For another example, do not ask the assistant to wake you up at 5pm or set a reminder because it cannot perform any action.
>5. The instructions should be in {language}.
>6. The instructions should be 1 to 4 sentences long. Either an imperative sentence or a question is permitted.
>7. You should generate an appropriate input to the instruction. The input field should contain a specific example provided for the instruction. It should involve realistic data and should not contain simple placeholders. The input should provide substantial content to make the instruction challenging but should ideally not exceed 300 words.
>8. Not all instructions require input. For example, when an instruction asks about some general information, "What is diabetes", it is not necessary to provide a specific context. In this case, we simply put "<noinput>" in the input field.
>9. The output should be an appropriate response to the instruction and the input. It should ideally not exceed 400 words.
>10. All generated output should use the metric system for measurements and UK names for medications, substances, drugs and everything else.
> 
> List of {quantity} tasks (every task has the following fields: Task:, Instruction:, Input:, Output:):

This prompt needs to be filled in with `{quantity}` and `{language}`. By default, it's in English. The [example config](https://github.com/CogStack/OpenGPT/blob/main/configs/example_config_for_detaset_creation.yaml) has quantity set to 10 and each prompt sent twice to the LLM. 

That's it! 

Everything else in the code base is just scaffolding. 

There are `4,688` examples in the Medical Tasks dataset. And if we are generating 10 each time, I'll prompt the LLM `500` times. 

The only data from OpenGPT that is in OH2.5 is the Medical Tasks dataset. You can see by running the `count_cogstack.py`. 

## ~~scrape info from NHS website~~

**NOTE: Before I thought we had to scrape the NHS website. However, I realized based on the prompt used for Medical Tasks that is the one version that doesn't actually take in a document.**

You can see here https://github.com/CogStack/OpenGPT/blob/main/experiments/Prompt%20Creation.ipynb that the prompt with the hash used for Medical Tasks has no `{context}` field. 

```
Description:  Generates high complexity various medical instruction-tasks
Hash:  5755564c19
```

We still have the scraped data here if we decide to use it later for some reason. https://huggingface.co/datasets/mlfoundations-dev/open_gpt_scrape.  

>We start by collecting a sizeable high-quality dataset in the healthcare domain. In my case, I scraped the Patient Information section of the NHS.UK website which contains definitions of diseases together with the corresponding symptoms and medications. In total, we collected the text from 2,354 pages. ([blog](https://aiforhealthcare.substack.com/p/a-large-language-model-for-healthcare))

We are using the https://www.nhs.uk/conditions/ page which is called `Health A to Z`. This looks like the main patient information page. This also aligns with the example data provided in the repo called [nhs_conditions_small_sample/original_data.csv](https://github.com/CogStack/OpenGPT/blob/main/data/nhs_conditions_small_sample/original_data.csv). Our scraping finds `1190 urls`. And `1,160` successful descriptions.

Example scraped and cleaned text from https://www.nhs.uk/conditions/angelman-syndrome/
> Angelman syndrome is a rare genetic condition that affects the nervous system and causes severe physical and learning disabilities. A person with Angelman syndrome will have a near-normal life expectancy, but they will need support throughout their life. 
>
> Characteristics of Angelman syndrome
> A child with Angelman syndrome will begin to show signs of delayed development at around 6 to 12 months of age, such as being unable to sit unsupported or make babbling noises. Later, they may not speak at all or may only be able to say a few words. However, most children with Angelman syndrome will be able to communicate using gestures, signs or other systems. The movement of a child with Angelman syndrome will also be affected. They may have difficulty walking because of issues with balance and co-ordination (ataxia). Their arms may tremble or make jerky movements, and their legs may be stiff. Several distinctive behaviours are associated with Angelman syndrome, although a child with the condition may not have all of these behaviours. They include:frequent laughter and smiling, often with little stimulusbeing easily excitable, often flapping the handsbeing restless (hyperactive)having a short attention spantrouble sleeping and needing less sleep than other childrena particular fascination with waterBy around 2 years of age, a small head which may also be flat at the back (microbrachycephaly) may be noticeable in some children with Angelman syndrome. Children with Angelman syndrome may also start to have seizures or fits around this age. Other possible features of the syndrome include:tendency to stick the tongue outcrossed eyes (strabismus)skin, hair and eyes that are paler than other family membersa wide mouth with widely spaced teetha side-to-side curvature of the spine (scoliosis)walking with arms in the airSome young babies with Angelman syndrome may have difficulties feeding because they're unable to co-ordinate sucking and swallowing. In such cases, they may need to be fed through a feeding tube. Babies with Angelman syndrome may need to be treated for reflux.
>
> Causes of Angelman syndrome
> In most cases of Angelman syndrome, the child's parents do not have the condition and the genetic difference responsible for the syndrome happens by chance around the time of conception. Angelman syndrome usually happens when the gene known as UBE3A is either missing or not working properly. A gene is a single unit of genetic material (DNA) that acts as an instruction for the way an individual is made and develops. Usually a child gets 2 copies of this gene, one from each parent, but only the gene from the mother is active. Most cases of Angelman syndrome are caused by the child not getting a copy of the UBE3A gene from its mother, or the gene not working. This means there's no active copy of the gene in the child's brain. In a small number of cases, Angelman syndrome happens when a child gets 2 inactive copies of the gene from their father, rather than 1 from each parent. Sometimes the cause of Angelman syndrome is unknown. Most children in these unexplained cases have different conditions involving other genes or chromosomes.
>
> Diagnosing Angelman syndrome
> Angelman syndrome may be suspected if a child's development is delayed and they have the syndrome's distinctive characteristics. A blood test is used to confirm the diagnosis. Several genetic tests will be done on the blood sample. These tests look for:any chromosomes or pieces of chromosomes that are missingchanges in the mother's or father's UBE3A gene that they may have passed onchanges in the child's UBE3A gene that would stop it from workingFor each child with Angelman syndrome, it's important to know the genetic change that caused the condition. This helps to determine your chance of having another child with Angelman syndrome. Most children with Angelman syndrome are diagnosed between the ages of 9 months to 6 years, when physical and behavioural symptoms become apparent. If your child is diagnosed with Angelman syndrome, you will be able to talk to a genetic doctor about what support they might need.
>
> Managing Angelman syndrome
> Your child may benefit from some of the following treatments and aids:anti-epileptic medicine to control seizuresphysiotherapy may improve posture, balance and walking ability; it's also important to prevent permanent stiffening of the joints as people with Angelman syndrome get oldercommunication therapy may help them develop non-verbal language skills, such as sign language and using visual aids, or ways to help them communicate such as Signalong, Makaton or PECS; using iPad applications and similar tablet devices may also helpbehavioural therapy may be recommended to help overcome behaviours you find hard to manage, such as hyperactivity and a short attention spanIn later childhood, the seizures usually improve, although they may return in adulthood. With age, people with Angelman syndrome become less hyperactive and may sleep better. Most people with the syndrome will have learning disability and limited speech throughout their life. In adults, some mobility may be lost and joints may stiffen. People with Angelman syndrome usually have good general health and are often able to improve their communication and acquire new skills. While there's currently no cure for Angelman syndrome, research into treatments is being done in other countries. There are also clinical trials looking at treatment for some of the symptoms associated with Angelman syndrome, such as seizures. Find out more about:how to care for a disabled childsupport and benefits for carers
>
> Help and support
> AngelmanUK is a charity providing information and support for parents and carers of people with Angelman syndrome. You can call their helpline (0300 999 0102) to speak with parents of people with Angelman syndrome, who can offer you advice and support. The Foundation for Angelman Syndrome Therapeutics (FAST) is a charity that provides information about Angelman syndrome. The website includes a section for parents who have a child who has recently been diagnosed with Angelman syndrome.
>
> National Congenital Anomaly and Rare Disease Registration Service
> If your child has Angelman syndrome, your clinical team will pass information about them on to the National Congenital Anomaly and Rare Disease Registration Service (NCARDRS). The NCARDRS helps scientists look for better ways to prevent and treat this condition. You can opt out of the register at any time.
