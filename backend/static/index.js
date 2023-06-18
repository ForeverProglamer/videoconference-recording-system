'use strict';

const SIGN_OUT_URI = '/api/users/sign-out'
const SCHEDULE_MEETING_URI = '/api/conferences'
const DELETE_MEETING_URI = '/api/conferences/'
const STOP_RECORDING_URI = '/api/conferences/{}/recording/stop'

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
        conferenceContainer.innerHTML += data
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

    function formatDatetimeToISO(datetimeValue) {
        // Create a new Date object using the datetime value
        const date = new Date(datetimeValue)
      
        // Get the user's local timezone offset in minutes
        const userTimezoneOffset = date.getTimezoneOffset()
      
        // Function to format the timezone offset (+/-HH:mm)
        const formatTimezoneOffset = (offset) => {
          const sign = offset < 0 ? '+' : '-'
          const hours = Math.abs(Math.floor(offset / 60)).toString().padStart(2, '0')
          const minutes = Math.abs(offset % 60).toString().padStart(2, '0')
          return `${sign}${hours}:${minutes}`
        };
      
        // Convert the user's timezone offset to the desired format
        const timezoneOffsetFormatted = formatTimezoneOffset(userTimezoneOffset)
      
        // Adjust the date by subtracting the user's timezone offset
        date.setMinutes(date.getMinutes() - userTimezoneOffset)
      
        // Get the ISO string representation of the adjusted date
        let isoString = date.toISOString()
      
        // Replace the "Z" in the ISO string with the formatted timezone offset
        isoString = isoString.replace('Z', timezoneOffsetFormatted)
      
        return isoString
    }

    const getScheduleFormData = () => {
        let startTime = formatDatetimeToISO(new Date())
        let endTime = undefined
        
        if (scheduleRecordingRadioButton.checked) {
            startTime = new Date(startTimeInput.value)
            endTime = new Date(endTimeInput.value)
            if (startTime >= endTime)
                throw new Error('End time can`t be earlier than start time')
            startTime = formatDatetimeToISO(startTime)
            endTime = formatDatetimeToISO(endTime)
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
                    headers: {'Accept': 'text/html', 'Content-Type': 'application/json'},
                    body: JSON.stringify(getScheduleFormData())
                }
            )
            console.log(response)
        } catch (error) {
            console.log(error)
            return
        }

        if (response.status !== 201) return

        const htmlResponse = await response.text()

        renderConference(htmlResponse)

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

// Stop conference recording
const stopRecording = async button => {
    const conferenceId = button.getAttribute('data-conference-id')
    const uri = STOP_RECORDING_URI.replace('{}', conferenceId)

    let response
    try {
        response = await fetch(`${location.origin}${uri}`, {method: 'POST'})
    } catch (error) {
        console.error(error)
        return
    }

    console.log(response)
}