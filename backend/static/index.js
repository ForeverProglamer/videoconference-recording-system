'use strict';

const SIGN_OUT_URI = '/api/users/sign-out'
const SCHEDULE_MEETING_URI = '/api/conferences'
const DELETE_MEETING_URI = '/api/conferences/'

const ZOOM_LOGO_URI = '/static/img/zoom.svg'
const MEET_LOGO_URI = '/static/img/meet.png'

const LOGO_URI = {
    'zoom': ZOOM_LOGO_URI,
    'google_meet': MEET_LOGO_URI
}

const RECORDING_STATUS_TO_HTML = {
    'scheduled': {
        icon: '<i class="fa-solid fa-calendar-check"></i>',
        text: 'Scheduled'
    },
    'in_progress': {
        icon: '<i class="fa-solid fa-spinner"></i>',
        text: 'In progress'
    },
    'finished': {
        icon: '<i class="fa-solid fa-circle-check"></i>',
        text: 'Finished'
    }
}

const CONFERENCE_TEMPLATE = `
<div class="card mb-3">
    <div class="row g-0 justify-content-around align-items-center">
        <div class="col-2 py-2">
            <img width="80" height="80" src="{1}" 
                class="img-fluid rounded mx-auto d-block" 
                alt="Conferencing Platform Logo"
            >
        </div>
        <div class="col-1 vr"></div>
        <div class="col-7 py-2">
            <h5 class="card-title">{2}</h5>
            <div>
                <span class="me-2">
                    <i class="fa-solid fa-calendar-week"></i> {3}
                </span>
                <span class="me-2">
                    <i class="fa-solid fa-clock"></i> {4}
                </span>
            </div>
            <div>
                <span class="me-2">
                    <i class="fa-solid fa-circle-user"></i> {5}
                </span>
                <span class="me-2">
                    <i class="fa-solid fa-link"></i>
                    <a href="{6}" class="card-text">Invite link</a>
                </span>
                <span>{7}</span>
            </div>
        </div>
        <div class="col-2 py-2">
            <button data-conference-id="{0}" 
                class="btn btn-outline-primary mb-3 w-100" 
            >Edit</button>
        
            <button data-conference-id="{0}" 
                class="btn btn-outline-danger w-100" 
                onclick="deleteConference(this)"
            >Delete</button>
        </div>
    </div>
</div>
`


function formatTemplate(template, ...args) {
    let result = template.slice()
    for (let i = 0; i < args.length; i++) {
        let regexp = new RegExp('\\{'+i+'\\}', 'gi')
        result = result.replace(regexp, args[i])
    }
    return result
}


window.addEventListener('DOMContentLoaded', event => {
    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault()
            document.body.classList.toggle('sb-sidenav-toggled')
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'))
        })
    }

    // Logic for sign out button
    const signOutButton = document.getElementById('signout')
    if (signOutButton) {
        signOutButton.addEventListener('click', async (event) => {
            event.preventDefault()
            const response = await fetch(
                `${location.origin}${SIGN_OUT_URI}`, {method: 'POST'}
            )
            console.log(response)
            document.location.reload()
        })
    }

    // Disabling start and end time inputs
    const instantRecordingRadioButton = document.getElementById('instantRecording')
    const scheduleRecordingRadioButton = document.getElementById('scheduleRecording')

    const startTimeInput = document.getElementById('startTime')
    const endTimeInput = document.getElementById('endTime')

    const handleRadioChange = () => {
        if (instantRecordingRadioButton.checked) {
            startTimeInput.disabled = true
            endTimeInput.disabled = true
        } else {
            startTimeInput.disabled = false
            endTimeInput.disabled = false
        }
    }

    handleRadioChange()

    instantRecordingRadioButton.addEventListener('change', handleRadioChange)
    scheduleRecordingRadioButton.addEventListener('change', handleRadioChange)


    // Conference rendering
    const conferenceContainer = document.getElementById('conferencesContainer')

    function renderConference(data) {
        const leftSpaceDiv = document.createElement('div')
        leftSpaceDiv.className = 'col-md-1'
        leftSpaceDiv.setAttribute('data-conference-id', data.id)
        
        const conferenceDiv = document.createElement('div')
        conferenceDiv.className = 'col-md-10'
        conferenceDiv.setAttribute('data-conference-id', data.id)
        conferenceDiv.innerHTML = mapConferenceToHTML(data)

        const rightSpaceDiv = document.createElement('div')
        rightSpaceDiv.className = 'col-md-1'
        rightSpaceDiv.setAttribute('data-conference-id', data.id)

        conferenceContainer.appendChild(leftSpaceDiv)
        conferenceContainer.appendChild(conferenceDiv)
        conferenceContainer.appendChild(rightSpaceDiv)
    }

    function mapConferenceToHTML(data) {
        const imgHref = `${location.origin}${LOGO_URI[data['platform']]}`

        const startTime = new Date(data['start_time'])
        const date = startTime.toDateString().split(' ').slice(0, 3).join(' ')
        const time = startTime.toTimeString().split(':').slice(0, 2).join(':')

        const status = data['recording']['status']
        const htmlStatus = RECORDING_STATUS_TO_HTML[status]
        
        const renderedTemplate = formatTemplate(
            CONFERENCE_TEMPLATE,
            data['id'],
            imgHref,
            data['title'],
            date,
            time,
            data['settings']['participant_name'],
            data['invite_link'],
            `${htmlStatus.icon} ${htmlStatus.text}`
        )

        return renderedTemplate
    }

    // Schedule conference form handling
    const titleInput = document.getElementById('title')
    const platformSelect = document.getElementById('platform')
    const inviteLinkInput = document.getElementById('inviteLink')
    const participantNameInput = document.getElementById('participantName')
    const diclaimerMessageInput = document.getElementById('disclaimerMessage')
    const scheduleButton = document.getElementById('scheduleBtn')

    const getScheduleFormData = () => {
        let startTime = new Date()
        let endTime = undefined
        
        if (scheduleRecordingRadioButton.checked) {
            startTime = new Date(startTimeInput.value)
            endTime = new Date(endTimeInput.value)
            if (startTime > endTime)
                throw new Error('End time can`t be earlier than start time')
        }

        if (platformSelect.selectedIndex === 0)
            throw new Error('One of meeting platforms must be selected')

        return {
            'title': titleInput.value,
            'invite_link': inviteLinkInput.value,
            'start_time': startTime,
            'end_time': endTime,
            'platform': platformSelect.value,
            'settings': {
                'participant_name': participantNameInput.value,
                'disclaimer_message': diclaimerMessageInput.value
            }
        }
    }

    const clearFormData = () => {
        titleInput.value = ''
        platformSelect.selectedIndex = 0
        inviteLinkInput.value = ''
        participantNameInput.value = ''
        diclaimerMessageInput.value = ''

        startTimeInput.value = ''
        endTimeInput.value = ''

        instantRecordingRadioButton.checked = true
        scheduleRecordingRadioButton.checked = false

        startTimeInput.disabled = true
        endTimeInput.disabled = true

    }

    const sendScheduleForm = async () => {
        let response

        try {
            response = await fetch(
                `${location.origin}${SCHEDULE_MEETING_URI}`,
                {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(getScheduleFormData())
                }
            )
            console.log(response)
        } catch (error) {
            console.log(error)
            return
        }
        const jsonResponse = await response.json()
        console.log(jsonResponse)

        renderConference(jsonResponse)

        clearFormData()
    }

    scheduleButton.addEventListener('click', sendScheduleForm)
})

// Remove conference from page
const removeConferenceFromPage = conferenceId => {
    document
        .querySelectorAll(`div[data-conference-id="${conferenceId}"]`)
        .forEach(div => div.remove())
}

// Delete conference
const deleteConference = async button => {
    const conferenceId = button.getAttribute('data-conference-id')
    let response

    try {
        response = await fetch(
            `${location.origin}${DELETE_MEETING_URI}${conferenceId}`,
             {method: 'DELETE'}
        )
        console.log(response)
    } catch (error) {
        console.error(error)
        return
    }

    if (response.status !== 204) {
        throw new Error(
            `Delete operation on conference with id ${conferenceId} failed`
        )
    }

    removeConferenceFromPage(conferenceId)
}