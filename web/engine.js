/**
 * Priority App — Client-side Core Engines
 * Faithful JavaScript implementation of backend algorithms:
 * - Scoring Engine (app/services/scoring_engine.py)
 * - Priority Engine (app/services/priority_engine.py)
 * - Safety Layer (app/services/safety_layer.py)
 */

export const HealthDimension = {
  SLEEP: 'sleep',
  STRESS: 'stress',
  NUTRITION: 'nutrition',
  HYDRATION: 'hydration',
  ACTIVITY: 'activity',
  RECOVERY: 'recovery',
  SCREEN_TIME: 'screen_time',
  CAFFEINE: 'caffeine',
};

export const ACTION_TEMPLATES = {
  [HealthDimension.SLEEP]: [
    "Set a hard stop for screens 30 minutes before your target bedtime tonight.",
    "Try to go to bed within 30 minutes of the same time as last night.",
    "If you can, fit in a 20-minute power nap this afternoon (before 3 PM to protect tonight's sleep)."
  ],
  [HealthDimension.STRESS]: [
    "Take a 5-minute breathing break: 4 counts in, 4 hold, 6 out.",
    "Write down the one thing stressing you most and one tiny step you can take on it today.",
    "Step outside for a 10-minute walk without your phone to let your nervous system reset."
  ],
  [HealthDimension.HYDRATION]: [
    "Fill a water bottle right now and keep it at your desk for the day.",
    "Drink a full glass of water before your next meal or class.",
    "Replace one cup of coffee or energy drink this afternoon with ice water."
  ],
  [HealthDimension.NUTRITION]: [
    "Eat a balanced meal in the next 90 minutes — focus on protein and greens.",
    "Grab a nutritious snack (fruit, almonds, yogurt) before your energy crashes.",
    "If you skipped breakfast, make lunch your non-negotiable priority today."
  ],
  [HealthDimension.ACTIVITY]: [
    "Take a brisk 15-minute walk between lectures or study blocks.",
    "Do a quick 10-minute stretch or light bodyweight routine right by your bed.",
    "Walk the long route to your next destination to get natural sunlight."
  ],
  [HealthDimension.RECOVERY]: [
    "Carve out 20 minutes for something genuinely restorative — not passive scrolling.",
    "Give yourself permission to decline one non-essential social commitment today.",
    "Wind down 30 minutes earlier tonight with calm music or reading."
  ],
  [HealthDimension.SCREEN_TIME]: [
    "Set your phone to grayscale mode for the rest of the day — it makes scrolling far less compelling.",
    "Pick one app that eats the most time and log out of it until tomorrow morning.",
    "Charge your phone outside the bedroom tonight and read a few pages of a book instead."
  ],
  [HealthDimension.CAFFEINE]: [
    "Make your next drink water or decaf — keep total caffeine today within your limit.",
    "No caffeine after 2 PM today so it doesn't interfere with tonight's sleep.",
    "Swap one coffee for a 10-minute walk — the alertness boost lasts longer."
  ]
};

// Safety Layer Keywords & Limits
export const CRISIS_KEYWORDS = [
  "kill myself", "want to die", "end it all", "suicide", "suicidal",
  "self-harm", "self harm", "cutting myself", "hurt myself",
  "don't want to be alive", "no reason to live", "better off dead",
  "can't go on", "can't take it anymore", "give up on everything"
];

export const DISORDERED_EATING_KEYWORDS = [
  "purging", "purge", "binge and purge", "making myself throw up",
  "throwing up on purpose", "laxatives to lose weight",
  "haven't eaten in days", "starving myself", "restricting food",
  "scared to eat", "afraid of food", "don't deserve to eat"
];

export const SUPPORT_RESOURCES = {
  title: "We're Here For You",
  message: "It sounds like you may be carrying an overwhelming amount right now. You don't have to carry this alone, and your health comes first.",
  resources: [
    { name: "988 Suicide & Crisis Lifeline", contact: "Call or text 988 (Free, 24/7, Confidential)", link: "tel:988" },
    { name: "Crisis Text Line", contact: "Text HOME to 741741 (24/7 Support)", link: "sms:741741" },
    { name: "Campus Student Counseling", contact: "Free student health & mental wellness center services", link: "#" },
    { name: "The Trevor Project (LGBTQ Youth)", contact: "Call 1-866-488-7386 or Text START to 678-678", link: "tel:18664887386" }
  ]
};

/**
 * Safety Layer Scanner
 */
export function checkSafety(currentCheckin, recentCheckins = []) {
  const flags = [];
  const notes = (currentCheckin.notes || '').toLowerCase();

  // 1. Check notes for crisis keywords
  for (const kw of CRISIS_KEYWORDS) {
    if (notes.includes(kw)) {
      flags.push({
        severity: 'critical',
        reason: `Crisis-related sentiment detected in notes ("${kw}").`
      });
      break;
    }
  }

  // 2. Check notes for disordered eating
  for (const kw of DISORDERED_EATING_KEYWORDS) {
    if (notes.includes(kw)) {
      flags.push({
        severity: 'critical',
        reason: 'Language related to disordered eating patterns detected in notes.'
      });
      break;
    }
  }

  // 3. Extreme sleep deprivation
  const sleep = currentCheckin.sleep_hours;
  if (sleep !== undefined && sleep !== null) {
    if (sleep <= 2.0) {
      let streak = 1;
      for (const past of recentCheckins) {
        if (past.sleep_hours !== undefined && past.sleep_hours <= 2.0) {
          streak++;
        } else {
          break;
        }
      }
      if (streak >= 3) {
        flags.push({
          severity: 'critical',
          reason: `Extreme sleep deprivation reported for ${streak} consecutive days (≤2.0 hrs).`
        });
      } else if (sleep === 0) {
        flags.push({
          severity: 'warning',
          reason: 'Zero hours of sleep reported last night.'
        });
      }
    }
  }

  // 4. Consecutive Maximum Stress
  const stress = currentCheckin.stress_level;
  if (stress != null && stress >= 5) {
    let streak = 1;
    for (const past of recentCheckins) {
      if (past.stress_level >= 5) {
        streak++;
      } else {
        break;
      }
    }
    if (streak >= 5) {
      flags.push({
        severity: 'critical',
        reason: `Maximum stress level (5/5) reported for ${streak} consecutive days.`
      });
    }
  }

  // 5. Zero meals consecutive
  const meals = currentCheckin.meals_eaten;
  if (meals != null && meals === 0) {
    let streak = 1;
    for (const past of recentCheckins) {
      if (past.meals_eaten === 0) {
        streak++;
      } else {
        break;
      }
    }
    if (streak >= 2) {
      flags.push({
        severity: 'critical',
        reason: `Zero meals reported for ${streak} consecutive days.`
      });
    }
  }

  if (flags.length > 0) {
    const isCritical = flags.some(f => f.severity === 'critical');
    return {
      isFlagged: true,
      severity: isCritical ? 'critical' : 'warning',
      flagReason: flags[0].reason,
      support: SUPPORT_RESOURCES
    };
  }

  return { isFlagged: false };
}

/**
 * Compute Urgency per Dimension (Priority Engine)
 */
export function computeUrgency(dim, current, baseline) {
  if (current === null || current === undefined) return 0.0;

  switch (dim) {
    case HealthDimension.SLEEP:
      if (current <= 2.0) return 10.0;
      if (current <= 4.0) return 7.0;
      if (baseline && current < baseline * 0.75) return 6.0;
      if (baseline && current < baseline * 0.9) return 3.0;
      return 1.0;

    case HealthDimension.ACTIVITY:
      if (current === 0) return 5.0;
      if (current < 15) return 4.0;
      if (baseline && current < baseline * 0.5) return 3.5;
      return 1.0;

    case HealthDimension.HYDRATION:
      if (current <= 1) return 5.5;
      if (current <= 3) return 4.0;
      if (baseline && current < baseline * 0.6) return 3.0;
      return 1.0;

    case HealthDimension.STRESS:
      // Stress: higher is worse
      if (current >= 5) return 6.5;
      if (current >= 4) return 4.5;
      if (baseline && current > baseline * 1.4) return 3.5;
      return 1.0;

    case HealthDimension.NUTRITION:
      if (current === 0) return 6.0;
      if (current <= 1) return 4.5;
      if (baseline && current < baseline * 0.6) return 3.0;
      return 1.0;

    case HealthDimension.RECOVERY:
      if (current <= 1.5) return 5.5;
      if (current <= 2.5) return 4.0;
      if (baseline && current < baseline * 0.7) return 3.0;
      return 1.0;

    case HealthDimension.SCREEN_TIME:
      // Higher = worse (inverted dimension)
      if (current > 12.0) return 6.0;
      if (current > 9.0) return 4.5;
      if (baseline && current > baseline * 1.4) return 3.5;
      if (baseline && current > baseline * 1.2) return 2.0;
      return 1.0;

    case HealthDimension.CAFFEINE:
      // Higher = worse (inverted dimension)
      if (current >= 6) return 5.0;
      if (current >= 4) return 3.5;
      if (baseline && current > baseline * 1.5) return 2.5;
      return 1.0;

    default:
      return 1.0;
  }
}

/**
 * Determine the ONE Top Priority
 */
export function determinePriority(currentCheckin, profile, recentCheckins = [], recentPriorities = []) {
  // Check safety first
  const safety = checkSafety(currentCheckin, recentCheckins);
  if (safety.isFlagged && safety.severity === 'critical') {
    return {
      safetyFlagged: true,
      safetyMessage: safety.flagReason,
      support: safety.support,
      priorityDimension: HealthDimension.RECOVERY,
      priorityReason: "Emergency safety protocol activated. Please step away from tasks and access student support resources.",
      suggestedActions: [
        "Reach out to your campus counseling line or text HOME to 741741.",
        "Take 5 deep breaths in a quiet, safe environment.",
        "Let a trusted roommate, friend, or advisor know how you're feeling right now."
      ],
      urgencyScores: {}
    };
  }

  // Baselines from profile or student defaults
  const baselines = {
    [HealthDimension.SLEEP]: profile?.typical_sleep_hours || 7.5,
    [HealthDimension.STRESS]: 2.5,
    [HealthDimension.HYDRATION]: 6.0,
    [HealthDimension.NUTRITION]: 3.0,
    [HealthDimension.ACTIVITY]: 30.0,
    [HealthDimension.RECOVERY]: 3.5,
    [HealthDimension.SCREEN_TIME]: profile?.goal_max_screen_hours || 6.0,
    [HealthDimension.CAFFEINE]: profile?.goal_max_caffeine_cups || 3.0
  };

  // Values from checkin (null-safe for optional new fields)
  const values = {
    [HealthDimension.SLEEP]: currentCheckin.sleep_hours,
    [HealthDimension.STRESS]: currentCheckin.stress_level,
    [HealthDimension.HYDRATION]: currentCheckin.water_glasses,
    [HealthDimension.NUTRITION]: currentCheckin.meals_eaten,
    [HealthDimension.ACTIVITY]: currentCheckin.activity_minutes ?? (currentCheckin.stress_level >= 4 ? 10 : 30),
    [HealthDimension.RECOVERY]: ((currentCheckin.energy_level || 3) + (currentCheckin.mood || 3)) / 2.0,
    [HealthDimension.SCREEN_TIME]: currentCheckin.screen_time_hours ?? null,
    [HealthDimension.CAFFEINE]: currentCheckin.caffeine_cups ?? null
  };

  // Compute urgency for each dimension
  const urgencyMap = {};
  for (const dim of Object.values(HealthDimension)) {
    urgencyMap[dim] = computeUrgency(dim, values[dim], baselines[dim]);
  }

  // Diminishing returns modifier
  if (recentPriorities.length >= 3) {
    const lastThree = recentPriorities.slice(0, 3);
    const allSame = lastThree.every(d => d === lastThree[0]);
    if (allSame && urgencyMap[lastThree[0]]) {
      urgencyMap[lastThree[0]] *= 0.7; // 30% reduction to allow rotation
    }
  }

  // Sort by urgency descending
  const sorted = Object.entries(urgencyMap).sort((a, b) => b[1] - a[1]);
  const [topDim, topUrgency] = sorted[0];

  // Build empathetic explanation tailored to students
  let explanation = "";
  const curVal = values[topDim];
  const bVal = baselines[topDim];

  if (topUrgency <= 1.0) {
    explanation = `Your vitals are steady and well-balanced today. We're pointing your daily spotlight toward ${topDim.toUpperCase()} for an extra energy edge without adding any pressure.`;
  } else {
    switch (topDim) {
      case HealthDimension.SLEEP:
        explanation = `You logged ${curVal} hrs of sleep last night against your regular baseline of ${bVal} hrs. Sleep debt compounds fast during college terms — tonight, your single best lever is an intentional wind-down.`;
        break;
      case HealthDimension.STRESS:
        explanation = `Your stress is sitting at ${curVal}/5 today. When academic pressure peaks, cognitive fatigue sets in. Focusing on one calming release now protects the rest of your week.`;
        break;
      case HealthDimension.HYDRATION:
        explanation = `You've had only ${curVal} glasses of water. Even 2% dehydration cuts concentration and energy in half during lectures. A quick hydration boost will immediately clear mental fog.`;
        break;
      case HealthDimension.NUTRITION:
        explanation = `You've logged ${curVal} meals today. Skipping meals causes afternoon glucose dips and spikes anxiety. Giving your brain solid fuel is your highest payoff action today.`;
        break;
      case HealthDimension.ACTIVITY:
        explanation = `Long study hours keep your body in a stagnant posture. Just 15 minutes of walking or gentle stretching increases cerebral blood flow and resets your focus.`;
        break;
      case HealthDimension.RECOVERY:
        explanation = `Your system is asking for intentional decompression. Taking 20 minutes to truly unplug will make your study time dramatically more efficient later.`;
        break;
      case HealthDimension.SCREEN_TIME:
        explanation = `You've logged ${curVal} hours of screen time today, past your ${bVal}-hour limit. Late-night scrolling delays sleep onset and fragments deep sleep — a hard screen curfew tonight is your highest-leverage fix.`;
        break;
      case HealthDimension.CAFFEINE:
        explanation = `You've had ${curVal} caffeinated drinks today, over your ${bVal}-cup limit. Excess caffeine lingers 6+ hours in your system, quietly inflating stress and stealing sleep — cutting back now pays off tonight.`;
        break;
    }
  }

  const actions = ACTION_TEMPLATES[topDim] || ACTION_TEMPLATES[HealthDimension.RECOVERY];

  return {
    id: `rec-${Date.now()}`,
    safetyFlagged: safety.isFlagged,
    safetyMessage: safety.isFlagged ? safety.flagReason : null,
    support: safety.support || null,
    priorityDimension: topDim,
    priorityReason: explanation,
    llmExplanation: explanation,
    isCompleted: false,
    actions: actions.map((act, idx) => ({
      id: `act-${idx}`,
      actionText: act,
      order: idx + 1,
      isCompleted: false
    })),
    urgencyScores: urgencyMap,
    values,
    baselines
  };
}

/**
 * Generate 7-Day Student Archetype Data (Priya & Marcus)
 */
export function getPresetStudent(type) {
  if (type === 'priya') {
    // Priya — Overloaded Pre-Med
    return {
      profile: {
        name: "Priya Patel",
        role: "Sophomore • Biology (Pre-Med)",
        avatar: "👩🏽‍🔬",
        typical_sleep_hours: 7.5,
        target_water: 8,
        themeColor: "#2D5A43",
        bio: "Organic chemistry labs, MCAT prep, hospital volunteering. Struggles with chronic sleep debt and coffee overconsumption."
      },
      history: [
        { date: "Day -6", sleep_hours: 5.5, stress_level: 4, meals_eaten: 2, water_glasses: 3, activity_minutes: 15, screen_time_hours: 7.5, caffeine_cups: 3, notes: "O-chem quiz prep late night" },
        { date: "Day -5", sleep_hours: 4.5, stress_level: 5, meals_eaten: 2, water_glasses: 2, activity_minutes: 10, screen_time_hours: 9.0, caffeine_cups: 4, notes: "Lab report due at midnight" },
        { date: "Day -4", sleep_hours: 5.0, stress_level: 4, meals_eaten: 1, water_glasses: 4, activity_minutes: 20, screen_time_hours: 8.0, caffeine_cups: 3, notes: "Skipped breakfast again" },
        { date: "Day -3", sleep_hours: 8.5, stress_level: 3, meals_eaten: 3, water_glasses: 5, activity_minutes: 25, screen_time_hours: 5.0, caffeine_cups: 1, notes: "Sunday catch-up crash" },
        { date: "Day -2", sleep_hours: 5.0, stress_level: 4, meals_eaten: 2, water_glasses: 3, activity_minutes: 15, screen_time_hours: 8.5, caffeine_cups: 4, notes: "Monday 8 AM anatomy lecture" },
        { date: "Day -1", sleep_hours: 4.0, stress_level: 5, meals_eaten: 2, water_glasses: 2, activity_minutes: 10, screen_time_hours: 10.0, caffeine_cups: 5, notes: "Only 4 hours sleep, chugged 3 coffees" }
      ],
      todayInitial: {
        sleep_hours: 4.5,
        stress_level: 5,
        meals_eaten: 2,
        water_glasses: 3,
        activity_minutes: 10,
        screen_time_hours: 9.5,
        caffeine_cups: 4,
        notes: "Exhausted, midterms coming up in 2 days"
      }
    };
  } else if (type === 'marcus') {
    // Marcus — Social Night Owl
    return {
      profile: {
        name: "Marcus Vance",
        role: "Senior • Communications",
        avatar: "🎧",
        typical_sleep_hours: 7.0,
        target_water: 7,
        themeColor: "#3D5A80",
        bio: "Late restaurant closing shifts, erratic meal schedule, social gaming until 3 AM, inconsistent hydration."
      },
      history: [
        { date: "Day -6", sleep_hours: 6.0, stress_level: 2, meals_eaten: 2, water_glasses: 3, activity_minutes: 40, screen_time_hours: 6.0, caffeine_cups: 2, notes: "Pickup basketball at rec center" },
        { date: "Day -5", sleep_hours: 5.5, stress_level: 3, meals_eaten: 1, water_glasses: 2, activity_minutes: 15, screen_time_hours: 7.0, caffeine_cups: 3, notes: "Late shift at pub until 1 AM" },
        { date: "Day -4", sleep_hours: 6.5, stress_level: 3, meals_eaten: 2, water_glasses: 3, activity_minutes: 20, screen_time_hours: 8.5, caffeine_cups: 2, notes: "Ordered midnight pizza" },
        { date: "Day -3", sleep_hours: 5.0, stress_level: 4, meals_eaten: 2, water_glasses: 2, activity_minutes: 10, screen_time_hours: 9.5, caffeine_cups: 4, notes: "Gaming with roommates till 3:30 AM" },
        { date: "Day -2", sleep_hours: 6.0, stress_level: 3, meals_eaten: 2, water_glasses: 4, activity_minutes: 30, screen_time_hours: 7.5, caffeine_cups: 3, notes: "Job applications stressing me a bit" },
        { date: "Day -1", sleep_hours: 5.2, stress_level: 4, meals_eaten: 1, water_glasses: 2, activity_minutes: 10, screen_time_hours: 8.0, caffeine_cups: 4, notes: "Missed dinner, drank energy drink" }
      ],
      todayInitial: {
        sleep_hours: 5.0,
        stress_level: 4,
        meals_eaten: 1,
        water_glasses: 2,
        activity_minutes: 15,
        screen_time_hours: 8.5,
        caffeine_cups: 4,
        notes: "Slept at 2:45 AM, woke up dizzy, need to lock in"
      }
    };
  } else {
    // Clean Slate / Custom User
    return {
      profile: {
        name: "Alex Rivera",
        role: "College Student",
        avatar: "🎓",
        typical_sleep_hours: 7.5,
        target_water: 8,
        themeColor: "#2D5A43",
        bio: "Finding balance across coursework, health, and campus life."
      },
      history: [
        { date: "Day -6", sleep_hours: 7.0, stress_level: 2, meals_eaten: 3, water_glasses: 6, activity_minutes: 30, screen_time_hours: 5.5, caffeine_cups: 1, notes: "" },
        { date: "Day -5", sleep_hours: 6.5, stress_level: 3, meals_eaten: 3, water_glasses: 5, activity_minutes: 25, screen_time_hours: 6.0, caffeine_cups: 2, notes: "" },
        { date: "Day -4", sleep_hours: 7.5, stress_level: 2, meals_eaten: 3, water_glasses: 7, activity_minutes: 45, screen_time_hours: 4.5, caffeine_cups: 1, notes: "" },
        { date: "Day -3", sleep_hours: 8.0, stress_level: 1, meals_eaten: 3, water_glasses: 6, activity_minutes: 35, screen_time_hours: 5.0, caffeine_cups: 1, notes: "" },
        { date: "Day -2", sleep_hours: 6.0, stress_level: 3, meals_eaten: 2, water_glasses: 4, activity_minutes: 20, screen_time_hours: 7.0, caffeine_cups: 3, notes: "" },
        { date: "Day -1", sleep_hours: 6.8, stress_level: 3, meals_eaten: 3, water_glasses: 5, activity_minutes: 30, screen_time_hours: 6.0, caffeine_cups: 2, notes: "" }
      ],
      todayInitial: {
        sleep_hours: 7.0,
        stress_level: 3,
        meals_eaten: 3,
        water_glasses: 5,
        activity_minutes: 30,
        screen_time_hours: 5.5,
        caffeine_cups: 2,
        notes: ""
      }
    };
  }
}
