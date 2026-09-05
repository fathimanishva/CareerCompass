from models import CareerRole, Skill, UserSkill, CareerSkillRequirement, db

PROFICIENCY_SCORES = {
    'Beginner': 0.5,
    'Intermediate': 0.8,
    'Advanced': 1.0
}

IMPORTANCE_WEIGHTS = {
    'Critical': 3,
    'Recommended': 2,
    'Optional': 1
}

def analyze_skill_gap(user, career_role):
    """
    Computes a detailed skill gap analysis between a user's skills and a career role.
    Returns:
    {
        'career': CareerRole,
        'match_score': float (0-100),
        'readiness_level': str,
        'readiness_badge': str,
        'time_estimate': str,
        'matched_skills': list of dicts,
        'missing_critical_skills': list of dicts,
        'missing_recommended_skills': list of dicts,
        'missing_optional_skills': list of dicts,
        'radar_chart_data': dict (labels, user_scores, benchmark_scores),
        'acquired_count': int,
        'total_required_count': int
    }
    """
    # Build dictionary of user skills: {skill_id: UserSkill}
    user_skills = UserSkill.query.filter_by(
            user_id=user.id
        ).all()

        user_skill_map = {
            us.skill_id: us
            for us in user_skills
        }
    
    requirements = CareerSkillRequirement.query.filter_by(career_id=career_role.id).all()
    
    total_possible_weight = 0
    earned_weight = 0
    
    matched_skills = []
    missing_critical = []
    missing_recommended = []
    missing_optional = []
    
    radar_labels = []
    radar_user_scores = []
    radar_target_scores = []
    
    for req in requirements:
        skill = req.skill
        weight = IMPORTANCE_WEIGHTS.get(req.importance, 2)
        total_possible_weight += weight * 1.0  # target is full proficiency (1.0)
        
        target_score = 100
        user_score = 0
        
        if req.skill_id in user_skill_map:
            us = user_skill_map[req.skill_id]
            prof_mult = PROFICIENCY_SCORES.get(us.proficiency, 0.7)
            earned_weight += weight * prof_mult
            user_score = int(prof_mult * 100)
            
            matched_skills.append({
                'skill': skill,
                'user_proficiency': us.proficiency,
                'target_proficiency': req.target_proficiency,
                'importance': req.importance,
                'score_pct': user_score
            })
        else:
            missing_item = {
                'skill': skill,
                'importance': req.importance,
                'target_proficiency': req.target_proficiency,
                'weight': weight
            }
            if req.importance == 'Critical':
                missing_critical.append(missing_item)
            elif req.importance == 'Recommended':
                missing_recommended.append(missing_item)
            else:
                missing_optional.append(missing_item)
                
        radar_labels.append(skill.name)
        radar_user_scores.append(user_score)
        radar_target_scores.append(target_score)
        
    match_score = 0.0
    if total_possible_weight > 0:
        match_score = round((earned_weight / total_possible_weight) * 100, 1)
        
    # Cap between 0 and 100
    match_score = min(100.0, max(0.0, match_score))
    
    # Assess readiness
    if match_score >= 80:
        readiness_level = "Job Ready / Advanced Match"
        readiness_badge = "success"
        time_estimate = "1 - 3 Weeks (Final Portfolio & Interview Prep)"
    elif match_score >= 55:
        readiness_level = "Moderate Gap (Solid Foundation)"
        readiness_badge = "primary"
        time_estimate = "4 - 8 Weeks (Targeted Learning & Projects)"
    elif match_score >= 30:
        readiness_level = "Developing Skills"
        readiness_badge = "warning"
        time_estimate = "2 - 4 Months (Core Frameworks & Tools)"
    else:
        readiness_level = "Early Stage / Foundational"
        readiness_badge = "danger"
        time_estimate = "3 - 6 Months (Foundational Roadmap)"
        
    return {
        'career': career_role,
        'match_score': match_score,
        'readiness_level': readiness_level,
        'readiness_badge': readiness_badge,
        'time_estimate': time_estimate,
        'matched_skills': matched_skills,
        'missing_critical_skills': missing_critical,
        'missing_recommended_skills': missing_recommended,
        'missing_optional_skills': missing_optional,
        'radar_chart_data': {
            'labels': radar_labels[:10],  # top 10 for clean radar visual
            'user_scores': radar_user_scores[:10],
            'benchmark_scores': radar_target_scores[:10]
        },
        'acquired_count': len(matched_skills),
        'total_required_count': len(requirements)
    }


def find_top_career_matches(user, limit=5):
    """
    Efficiently ranks all career paths for the user.
    """

    # Load once
    all_careers = CareerRole.query.all()
    user_skills = UserSkill.query.filter_by(user_id=user.id).all()

    user_skill_map = {
        us.skill_id: us for us in user_skills
    }

    # Load all requirements once
    all_requirements = CareerSkillRequirement.query.all()

    # Group requirements by career
    requirements_by_career = {}

    for req in all_requirements:
        requirements_by_career.setdefault(
            req.career_id, []
        ).append(req)

    rankings = []

    for career in all_careers:

        requirements = requirements_by_career.get(
            career.id, []
        )

        total_possible_weight = 0
        earned_weight = 0

        matched_skills = []
        missing_critical_count = 0

        for req in requirements:

            weight = IMPORTANCE_WEIGHTS.get(
                req.importance, 2
            )

            total_possible_weight += weight

            if req.skill_id in user_skill_map:

                us = user_skill_map[req.skill_id]

                prof_mult = PROFICIENCY_SCORES.get(
                    us.proficiency, 0.7
                )

                earned_weight += weight * prof_mult

                matched_skills.append({
                    'skill': req.skill,
                    'user_proficiency': us.proficiency,
                    'target_proficiency': req.target_proficiency,
                    'importance': req.importance,
                    'score_pct': int(prof_mult * 100)
                })

            elif req.importance == 'Critical':
                missing_critical_count += 1

        if total_possible_weight > 0:
            match_score = round(
                (earned_weight / total_possible_weight) * 100,
                1
            )
        else:
            match_score = 0.0

        if match_score >= 80:
            readiness_level = "Job Ready / Advanced Match"
            readiness_badge = "success"

        elif match_score >= 55:
            readiness_level = "Moderate Gap (Solid Foundation)"
            readiness_badge = "primary"

        elif match_score >= 30:
            readiness_level = "Developing Skills"
            readiness_badge = "warning"

        else:
            readiness_level = "Early Stage / Foundational"
            readiness_badge = "danger"

        rankings.append({
            'career': career,
            'match_score': match_score,
            'readiness_level': readiness_level,
            'readiness_badge': readiness_badge,
            'acquired_count': len(matched_skills),
            'total_required_count': len(requirements),
            'missing_critical_count': missing_critical_count,
            'matched_skills': matched_skills
        })

    rankings.sort(
        key=lambda x: x['match_score'],
        reverse=True
    )

    return rankings[:limit]