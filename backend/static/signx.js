'use strict';

const URL = 'http://localhost:8000'

const PATHNAMES = new Map([
    ['/sign-in', '/api/users/sign-in'],
    ['/sign-up', '/api/users/sign-up']
])

const loginInput = document.getElementById('inputLogin')
const passwordInput = document.getElementById('inputPassword')
const confirmPasswordInput = document.getElementById('inputPasswordConfirm')

const submitBtn = document.getElementById('submitButton')
submitBtn.addEventListener('click', sendPost(location.pathname))

const errorContainer = {
    element: document.getElementById('error-message'),

    displayMessage(message) {
        this.element.innerText = message
        this.element.style.display = ''
    },

    clearMessage() {
        this.element.innerText = ''
        this.element.style.display = 'none'
    },

    isDisplayed() {
        return this.element.style.display === ''
    }
}

function sendPost(pathname) {
    if (!PATHNAMES.has(pathname)) {
        console.error(`Unsupported pathname given: ${pathname}`)
        throw new Error(`Unsupported pathname given: ${pathname}`)
    }

    const uri = PATHNAMES.get(pathname)

    return async () => {
        const data = {
            'login': loginInput.value,
            'password': passwordInput.value
        }
    
        if (confirmPasswordInput &&
            passwordInput.value !== confirmPasswordInput.value
        ) {
            errorContainer.displayMessage('Given two different passwords')
            return
        }

        let response
        try {
            response = await fetch(`${URL}${uri}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                redirect: 'follow',
                body: JSON.stringify(data)
            })
            console.log(response)
        } catch (error) {
            console.error(error)
            return
        }
        
        if (response.status !== 200) {
            const json = await response.json()
            console.error(json['detail'])
            errorContainer.displayMessage(json['detail'])
            return
        }
        
        if (errorContainer.isDisplayed()) errorContainer.clearMessage()

        if (pathname === '/sign-up') document.location.pathname = '/sign-in'
        else document.location.reload()
    }
}
