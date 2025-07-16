// Military abbreviation correction data models
template_string ChainOfThought(action: string?) #"
    Before you answer, please explain your reasoning step-by-step of choosing the abbreviation.
    {% if action %}{{ action }}{% endif %}
    
"#

class TeachingMaterial {
  text_en string
  text_ar string
  context string?
}

class ClosestAbbreviation {
  original string
  closest string
  confidence string
  decoding map<string,string> @description(#"
    What each letter in the Abbreviation stands for
  "#)
  reasoning string
}


// Function to correct altered military abbreviations in teaching materials
function DecodeMilitaryAbbreviations(material: TeachingMaterial) -> ClosestAbbreviation {
  client "VLLM2"
  prompt #"
    You are an expert in military terminology and abbreviations.

    
    For each abbreviation found:
    1. map the abbreviation to the closest common militay term 
    2. Determine the correct military abbreviation decoding
    3. Assess confidence level (High/Medium/Low)
    4. Provide the full meaning
    5. Explain your reasoning for the correction

    Text to analyze:
      {{ material.text_en }}
      {{ material.text_ar }}
    
    There is also extra context that can be of help: {{material.context}}

    {{ ctx.output_format }}
     {{ ChainOfThought("Determine the closest military abbreviation") }}
  "#
}

// Test basic VUCA alteration
test test_vuca_correction {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "Remember the VUCAR framework when analyzing the battlefield environment."
      text_ar "يشرح عناصر إطار عمل نموذج تدريب وتعليم القيادة في معهد القوات الجوية والدفاع الجوي" 
      context " VUCAR is a military term that is used in AFADI that maps to VUCA but the R stands for Resilience"
    }
  }
}

// Test multiple abbreviations
test test_multiple_corrections {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "State the meaning of \"PEA\" and \"NEA\"."
      text_ar " يبين معنى عامل الجذب العاطفي الإيجابي وعامل الجذب العاطفي السلبي "
    }
  }
}


// Test tactical abbreviations
test test_tactical_abbreviations {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "Complete your METT-CT analysis before developing the OPRD. Don't forget PACEE communications plan."
      text_ar "أكمل تحليل METT-CT قبل تطوير OPRD. لا تنس خطة الاتصالات PACEE"
      context ""
    }
  }
}

// Test intelligence abbreviations
test test_intelligence_abbreviations {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "Use PMSEII analysis for the region and apply CARVR methodology to identify targets."
      text_ar "استخدم تحليل PMSEII للمنطقة وطبق منهجية CARVR لتحديد الأهداف"
      context ""
    }
  }
}

// Test mixed alterations
test test_complex_alterations {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "During planning phase: 1) Conduct SWTO analysis 2) Use OAKOCK terrain assessment 3) Apply VUAC principles 4) Submit SITUPREP hourly"
      text_ar "خلال مرحلة التخطيط: 1) أجري تحليل SWTO 2) استخدم تقييم التضاريس OAKOCK 3) طبق مبادئ VUAC 4) قدم SITUPREP كل ساعة"
      context ""
    }
  }
}

// Test minimal alterations
test test_minimal_changes {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "Leadership must understand VUCA volatility and use MDNP process for decisions. Brief includes SMEACC format."
      text_ar "يجب على القيادة فهم تقلبات VUCA واستخدام عملية MDNP للقرارات. يشمل الإحاطة تنسيق SMEACC"
      context ""
    }
  }
}

// Test document with correct abbreviations
test test_no_corrections_needed {
  functions [DecodeMilitaryAbbreviations]
  args {
    material {
      text_en "Apply VUCA analysis using OODA loop. Standard METT-TC factors remain critical."
      text_ar "طبق تحليل VUCA باستخدام حلقة OODA. تبقى عوامل METT-TC المعيارية بالغة الأهمية"
      context ""
    }
  }
}