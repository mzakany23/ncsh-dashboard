def init_style():
    custom_css = '''
    :root {
        /* Apache Superset Color Palette */
        --primary: #20A7C9;         /* Superset blue */
        --primary-light: #66C2DA;   /* Lighter blue for hover states */
        --primary-dark: #1A85A0;    /* Darker blue for active states */

        /* Secondary Colors */
        --secondary: #484848;       /* Dark gray for headers and accents */
        --accent: #FF7F44;          /* Superset orange for highlights */

        /* Neutral Colors */
        --neutral-dark: #323232;    /* Dark gray for text */
        --neutral-medium: #666666;  /* Medium gray for secondary text */
        --neutral-light: #F5F5F5;   /* Light gray for backgrounds */
        --white: #FFFFFF;           /* White for cards and contrast */

        /* Semantic Colors */
        --success: #44B78B;         /* Green for positive metrics */
        --warning: #FCC700;         /* Yellow for neutral metrics */
        --danger: #E04355;          /* Red for negative metrics */

        /* UI Colors */
        --card-bg: var(--white);
        --body-bg: #F8F9FA;
        --border-color: #E0E0E0;
        --shadow-color: rgba(0, 0, 0, 0.05);
    }

    body {
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        background-color: var(--body-bg);
        color: var(--neutral-dark);
        font-size: 14px;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 600;
        color: var(--secondary);
    }

    p {
        color: var(--neutral-dark);
        line-height: 1.5;
    }

    .text-muted {
        color: var(--neutral-medium) !important;
    }

    /* Card Styles */
    .card {
        border-radius: 4px;
        box-shadow: 0 2px 6px var(--shadow-color);
        border: 1px solid var(--border-color);
        margin-bottom: 16px;
        background-color: var(--card-bg);
        overflow: hidden;
    }

    .card-header {
        background-color: var(--white);
        color: var(--secondary);
        font-weight: 600;
        padding: 12px 16px;
        border-bottom: 1px solid var(--border-color);
        font-size: 16px;
    }

    .card-header h4 {
        color: var(--secondary);
        margin: 0;
        font-size: 16px;
    }

    .card-body {
        padding: 16px;
    }

    /* Summary Cards */
    .summary-card {
        text-align: center;
    }

    .summary-card .card-header {
        background-color: var(--white);
        color: var(--secondary);
        border-bottom: 1px solid var(--border-color);
    }

    .summary-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
        margin: 10px 0;
    }

    /* Section headers */
    .section-header {
        margin-bottom: 0.75rem;
        color: #20A7C9;
        font-weight: 600;
        position: relative;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #F5F5F5;
        width: 100%;
    }

    .section-header-container {
        position: relative;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        width: 100%;
        border-bottom: 2px solid #F5F5F5;
        padding-bottom: 0.5rem;
    }

    /* Make sure HR tags extend fully */
    hr {
        width: 100%;
        margin: 1rem 0;
        border: none;
        border-top: 2px solid #F5F5F5;
    }

    /* Table Styles */
    .dash-table-container {
        border-radius: 4px;
        overflow: hidden;
        box-shadow: 0 1px 3px var(--shadow-color);
    }

    .dash-header {
        background-color: var(--neutral-light) !important;
        color: var(--secondary) !important;
        font-weight: 600 !important;
        border-bottom: 1px solid var(--border-color) !important;
    }

    /* Results styling */
    .result-win {
        background-color: rgba(68, 183, 139, 0.1) !important;
        border-left: 3px solid var(--success) !important;
    }

    .result-draw {
        background-color: rgba(252, 199, 0, 0.1) !important;
        border-left: 3px solid var(--warning) !important;
    }

    .result-loss {
        background-color: rgba(224, 67, 85, 0.1) !important;
        border-left: 3px solid var(--danger) !important;
    }

    /* Filter panel styling */
    .filter-panel {
        background-color: var(--card-bg);
        border-radius: 4px;
        padding: 20px;
        box-shadow: 0 1px 3px var(--shadow-color);
        border: 1px solid var(--border-color);
    }

    /* Dropdown styling */
    .Select {
        position: relative;
    }

    .Select-control {
        border-radius: 4px !important;
        border: 1px solid var(--border-color) !important;
        font-size: 14px !important;
        height: auto !important;
        min-height: 36px !important;
        background-color: var(--white) !important;
    }

    .Select-control:hover {
        border-color: var(--primary-light) !important;
    }

    .is-focused:not(.is-open) > .Select-control {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 0.2rem rgba(32, 167, 201, 0.25) !important;
    }

    .Select-menu-outer {
        background-color: var(--white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        max-height: 300px !important;
        overflow-y: auto !important;
    }

    .Select-option {
        padding: 8px 12px !important;
        cursor: pointer !important;
        background-color: var(--white) !important;
        color: var(--neutral-dark) !important;
    }

    .Select-option:active,
    .Select-option.is-focused {
        background-color: var(--primary-light) !important;
        color: var(--white) !important;
    }

    /* Mobile-specific styles */
    @media (max-width: 768px) {
        .Select-option {
            padding: 12px !important;
            font-size: 16px !important;
        }

        .Select-control {
            min-height: 44px !important;
        }

        /* Hide Win/Loss Distribution chart */
        #opponent-analysis-section .row > div:first-child {
            display: none !important;
        }

        .summary-card {
            margin-bottom: 15px;
        }

        .section-header {
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .summary-value {
            font-size: 1.8rem;
        }

        .filter-panel {
            padding: 16px;
        }

        .filter-panel .form-label {
            margin-top: 16px;
            margin-bottom: 8px;
        }

        .filter-panel .mb-2 {
            margin-bottom: 1rem !important;
        }

        .filter-panel .mb-4 {
            margin-bottom: 1.5rem !important;
        }

        /* Increase touch target size for radio buttons */
        .filter-panel .form-check {
            padding: 12px 0;
        }

        /* Make dropdowns more touch-friendly */
        .filter-panel .Select-control {
            min-height: 44px !important;
        }
    }

    /* Fix for iOS scrolling */
    .Select-menu {
        -webkit-overflow-scrolling: touch;
    }

    /* Ensure proper stacking context */
    #opponent-selection-div,
    #team-group-selection-div,
    #opponent-team-groups {
        position: relative !important;
        z-index: 1000 !important;
    }

    /* Multi-select dropdown styling */
    .Select--multi .Select-value {
        background-color: var(--primary-light) !important;
        border-color: var(--primary) !important;
        color: white !important;
        border-radius: 2px !important;
        margin-top: 3px !important;
        margin-bottom: 3px !important;
        max-width: 100% !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.4 !important;
        padding: 2px 5px !important;
    }

    .Select--multi .Select-value-icon {
        border-right-color: var(--primary) !important;
    }

    .Select--multi .Select-value-icon:hover {
        background-color: var(--primary) !important;
        color: white !important;
    }

    .Select-multi-value-wrapper {
        display: flex !important;
        flex-wrap: wrap !important;
        padding: 2px !important;
        max-width: 100% !important;
    }

    /* Date picker base styles */
    .DateRangePicker {
        width: 100% !important;
    }

    .DateRangePickerInput {
        background-color: var(--white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        display: flex !important;
        align-items: center !important;
        padding: 4px !important;
    }

    .DateInput {
        background: var(--white) !important;
        width: calc(50% - 20px) !important;
    }

    .DateInput_input {
        background-color: var(--white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        color: var(--neutral-dark) !important;
        font-size: 16px !important;
        padding: 8px !important;
        width: 100% !important;
    }

    .DateRangePickerInput_arrow {
        padding: 0 8px !important;
    }

    /* Calendar popup container */
    .DateRangePicker_picker {
        background-color: var(--white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 4px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        margin-top: 8px !important;
        z-index: 2000 !important;
    }

    /* Calendar month grid */
    .CalendarMonthGrid {
        background-color: var(--white) !important;
    }

    .CalendarMonth {
        background-color: var(--white) !important;
    }

    .CalendarMonth_caption {
        padding-bottom: 52px !important;
        color: var(--neutral-dark) !important;
    }

    /* Calendar days */
    .CalendarDay {
        background: var(--white) !important;
        border: 1px solid var(--border-color) !important;
        color: var(--neutral-dark) !important;
        font-size: 14px !important;
    }

    .CalendarDay__selected {
        background: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        color: var(--white) !important;
    }

    .CalendarDay__selected_span {
        background: var(--primary-light) !important;
        border: 1px solid var(--primary-light) !important;
        color: var(--white) !important;
    }

    .CalendarDay__hovered_span {
        background: var(--primary-light) !important;
        border: 1px solid var(--primary-light) !important;
        color: var(--white) !important;
    }

    /* Navigation buttons */
    .DayPickerNavigation_button {
        border: 1px solid var(--border-color) !important;
        background: var(--white) !important;
        color: var(--neutral-dark) !important;
    }

    /* Mobile specific styles */
    @media (max-width: 1024px) {
        .DateRangePicker_picker {
            position: fixed !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            margin: 0 !important;
            max-width: 95vw !important;
            width: 375px !important;
        }

        .DateRangePickerInput {
            min-height: 44px !important;
        }

        .DateInput_input {
            height: 44px !important;
            font-size: 16px !important;
        }

        .CalendarDay {
            min-width: 39px !important;
            height: 39px !important;
            line-height: 39px !important;
        }

        /* Ensure the calendar popup is above everything */
        .DayPicker_portal {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background-color: rgba(0, 0, 0, 0.5) !important;
            z-index: 2000 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
    }

    /* Button styling */
    .btn {
        border-radius: 4px;
        font-weight: 500;
        padding: 6px 12px;
        font-size: 14px;
    }

    .btn-primary {
        background-color: var(--primary);
        border-color: var(--primary);
    }

    .btn-primary:hover {
        background-color: var(--primary-dark);
        border-color: var(--primary-dark);
    }

    /* Chart container styling like Superset */
    .chart-container {
        padding: 0;
        border-radius: 4px;
        overflow: hidden;
        background-color: var(--white);
        border: 1px solid var(--border-color);
    }

    /* Loading Spinner Styles */
    .dash-spinner.dash-default-spinner {
        opacity: 0.7;
        width: 45px !important;
        height: 45px !important;
        border-width: 5px !important;
        border-color: var(--primary) !important;
        border-bottom-color: transparent !important;
        border-radius: 50% !important;
    }

    .dash-spinner.dash-circle-spinner {
        opacity: 0.7;
        width: 45px !important;
        height: 45px !important;
        border-width: 5px !important;
        border-color: var(--primary) !important;
        border-bottom-color: transparent !important;
        border-radius: 50% !important;
    }

    .dash-spinner-container {
        background-color: rgba(255, 255, 255, 0.8) !important;
    }

    /* Fullscreen loading overlay */
    ._dash-loading {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.85);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    ._dash-loading-callback::after {
        content: 'Loading dashboard...';
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 1.5rem;
        color: var(--primary);
        margin-top: 1rem;
        margin-left: -1rem;
    }

    ._dash-loading::before {
        content: '';
        display: block;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 6px solid var(--primary);
        border-color: var(--primary) transparent var(--primary) transparent;
        animation: dash-spinner 1.2s linear infinite;
    }

    @keyframes dash-spinner {
        0% {
            transform: rotate(0deg);
        }
        100% {
            transform: rotate(360deg);
        }
    }

    /* Fix for dropdown height to show full text */
    .Select.has-value.Select--multi .Select-input {
        margin-top: 3px !important;
    }

    /* Mobile menu styles */
    #mobile-menu {
        padding-top: 1rem;
        margin-top: 1rem;
        border-top: 1px solid var(--border-color);
    }

    #mobile-menu-button {
        background: none;
        border: none;
        padding: 0;
        font-size: 20px;
        color: var(--secondary);
        cursor: pointer;
    }

    #mobile-menu-button:hover {
        color: var(--primary);
    }

    @media (max-width: 768px) {
        .navbar-brand {
            font-size: 18px;
        }
    }

    /* AI Summary Section */
    #ai-summary-section {
        margin-top: 20px;
    }

    .ai-summary-content {
        padding: 15px;
        background-color: var(--white);
        border-radius: 4px;
        min-height: 100px;
    }

    .ai-summary-content h1,
    .ai-summary-content h2,
    .ai-summary-content h3 {
        color: var(--primary-color);
        margin-bottom: 10px;
    }

    .ai-summary-content h1 {
        font-size: 22px;
    }

    .ai-summary-content h2 {
        font-size: 20px;
    }

    .ai-summary-content h3 {
        font-size: 18px;
    }

    .ai-summary-content ul,
    .ai-summary-content ol {
        padding-left: 20px;
        margin-bottom: 10px;
    }

    .ai-summary-content li {
        margin-bottom: 5px;
    }

    .ai-summary-content p {
        margin-bottom: 10px;
        line-height: 1.5;
    }

    .ai-summary-content strong {
        font-weight: 600;
    }

    .ai-summary-content em {
        font-style: italic;
    }

    .ai-summary-content blockquote {
        border-left: 3px solid var(--primary-color);
        padding-left: 10px;
        margin: 10px 0;
        color: #555;
    }

    .ai-summary-content code {
        background-color: #f5f5f5;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: monospace;
    }

    /* Mobile adjustments for AI summary */
    @media (max-width: 1024px) {
        #generate-summary-button {
            width: 100%;
            margin-bottom: 15px;
        }

        .ai-summary-content {
            padding: 10px;
        }
    }

    /* AI Summary Icon and Container */
    .section-header-container {
        position: relative;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }

    .ai-icon-container {
        margin-left: 12px;
        display: inline-flex;
        align-items: center;
    }

    .btn-icon {
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .ai-icon {
        color: #20A7C9;
        font-size: 1.4rem;
        cursor: pointer;
        transition: transform 0.3s, color 0.3s;
        padding: 5px;
        background-color: rgba(32, 167, 201, 0.1);
        border-radius: 50%;
        box-shadow: 0 0 5px rgba(32, 167, 201, 0.2);
    }

    .ai-icon:hover {
        color: #147a95;
        transform: scale(1.15);
        background-color: rgba(32, 167, 201, 0.2);
        box-shadow: 0 0 8px rgba(32, 167, 201, 0.4);
    }

    /* AI Summary Content */
    .ai-summary-content {
        background-color: rgba(32, 167, 201, 0.05);
        border-left: 3px solid var(--primary-color);
        padding: 15px;
        border-radius: 4px;
        font-size: 0.95rem;
        line-height: 1.5;
        animation: fade-in 0.5s ease-in-out;
    }

    @keyframes fade-in {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .ai-summary-content h1,
    .ai-summary-content h2,
    .ai-summary-content h3 {
        color: var(--primary-color);
        margin-bottom: 10px;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .ai-summary-content p {
        margin-bottom: 10px;
    }

    .ai-summary-content strong {
        color: var(--secondary-color);
        font-weight: 600;
    }

    .ai-summary-content ul,
    .ai-summary-content ol {
        padding-left: 20px;
        margin-bottom: 10px;
    }

    .ai-summary-content li {
        margin-bottom: 5px;
    }

    /* Typing animation effect */
    .typing-animation {
        border-right: 2px solid var(--primary-color);
        animation: typing 1s steps(30, end) infinite;
    }

    @keyframes typing {
        from { border-color: var(--primary-color); }
        to { border-color: transparent; }
    }

    /* Mobile adjustments */
    @media (max-width: 1024px) {
        .ai-summary-content {
            padding: 10px;
        }
    }
    '''
    return custom_css