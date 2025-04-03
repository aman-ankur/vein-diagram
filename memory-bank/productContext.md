# Vein Diagram: Product Context

## Why This Project Exists

Vein Diagram addresses a critical gap in personal health management: the disconnect between receiving medical test results and actually understanding them in a meaningful context. Blood test results are typically delivered as static PDFs with raw numbers that fail to provide:

1. Historical context (how values have changed over time)
2. Relational insights (how different biomarkers influence each other)
3. Personalized interpretation (what these values mean for an individual's health)

This project exists to transform these static, often confusing documents into dynamic, insightful visualizations that empower users to take control of their health data and make informed decisions.

## Problems Solved

### For Health-Conscious Individuals & Families
- **Data Fragmentation**: Consolidates scattered test results from different labs and time periods into a single system, **organized by individual profiles** (e.g., for different family members).
- **Manual Data Entry**: Eliminates tedious and error-prone manual entry of biomarker values.
- **Trend Blindness**: Reveals patterns and trends **specific to each profile** that would be invisible when looking at individual test results.
- **Context Deficit**: Provides research-backed explanations about what biomarker values actually mean.
- **Information Overload**: Offers a summarized **Health Score** and a **Dashboard** view to provide an at-a-glance understanding of overall wellness based on key biomarkers.
- **Personalized Focus**: Allows users to **mark favorite biomarkers** for quick access and monitoring per profile, displayed prominently on the Dashboard.

### For Biohackers
- **Experiment Tracking**: Enables precise tracking of how interventions affect specific biomarkers **within their personal profile**.
- **Correlation Discovery**: Helps identify unexpected relationships between different health indicators.
- **Optimization Insights**: Facilitates data-driven health optimization through clear visualization of cause and effect.
- **Targeted Monitoring**: Use **favorite biomarkers** to quickly check key indicators affected by experiments.

### For Patients with Chronic Conditions
- **Condition Monitoring**: Simplifies the tracking of condition-specific biomarkers over time **within their profile**.
- **Treatment Effectiveness**: Shows clear evidence of whether treatments are working as expected.
- **Early Warning System**: Highlights concerning trends before they become serious health issues.
- **Focused Tracking**: Mark critical condition-related biomarkers as **favorites** for easy access.

## How It Should Work

### User Flow
1. **Profile Management**: User creates and manages distinct health profiles (e.g., self, family members).
2. **Upload**: User selects a profile and uploads PDF blood test results.
3. **Extraction**: System automatically extracts biomarker data, dates, and reference ranges, **associating them with the selected profile**.
4. **Dashboard**: User views a summary dashboard showing key information like favorite biomarkers, last report date, AI summary, and the Health Score **for the active profile**.
5. **Visualization**: Data is transformed into intuitive visualizations showing trends over time **for the active profile**.
6. **Favorite Tracking**: User marks key biomarkers as favorites **per profile**.
7. **Relationship Mapping**: Connections between related biomarkers are displayed.
8. **Health Score**: System calculates and displays an overall health score based on the profile's latest biomarker data against optimal ranges.
9. **Contextual Insights**: AI-powered explanations provide meaning and context for the data.
10. **Continued Use**: As users upload more test results to profiles, the system builds comprehensive health pictures for each individual, including score trends.

### Key Functionality
- PDF parsing with high accuracy across different lab formats.
- **Profile management** for organizing data for multiple individuals.
- **Dashboard view** summarizing key profile information (favorites, last report, AI summary, Health Score).
- Time-series visualization of biomarker trends **per profile**.
- **Favorite biomarker tracking** for personalized monitoring.
- Relationship mapping between correlated biomarkers.
- **Health Score calculation** providing a quick summary of wellness.
- AI-generated insights about biomarker meanings and relationships.
- User-friendly interface that makes complex health data accessible and personalized.

## User Experience Goals

### Simplicity
- Clean, uncluttered interface that doesn't overwhelm users with medical jargon
- Intuitive navigation that guides users naturally through their health data
- Streamlined upload process that works reliably with minimal user effort

### Insight
- Visualizations that reveal patterns not obvious from raw numbers
- Contextual information that helps users understand what their results mean
- Relationship maps that show how different aspects of health connect
- **Health Score** that provides a simple, understandable summary metric

### Empowerment
- Knowledge presented in a way that enables informed health decisions **for each profile**.
- Historical context that helps users see the effects of lifestyle changes **per individual**.
- Research-backed explanations that educate without overwhelming.
- **Personalization**: Ability to tailor the view and focus on what matters most to the user via profiles and favorites.

### Trust
- Transparent data handling that respects user privacy
- Clear indication of data sources and scientific backing
- Consistent reliability in data extraction and presentation

### Aesthetic Appeal
- Visually pleasing design that makes health data less clinical and more approachable
- Thoughtful color schemes that enhance understanding of data
- Modern, premium feel that elevates the experience of health tracking
