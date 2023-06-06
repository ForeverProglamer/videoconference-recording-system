from typing import Annotated

from fastapi import APIRouter, Cookie, status
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter(tags=['Pages'])

Token = Annotated[str | None, Cookie()]


@router.get('/sign-in')
def sign_in(token: Token = None):
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)
    content = """
        <html>
            <head>
                <title>Sign In Page</title>
            </head>
            <body>
                <h1>Please sign in</h1>
                <div>
                    <label for="uname"><b>Username</b></label>
                    <input type="text" placeholder="Enter Username" name="uname" required>
                    
                    <label for="psw"><b>Password</b></label>
                    <input type="password" placeholder="Enter Password" name="psw" required>
                    
                    <button type="submit" onclick="signInPost()">Sign In</button>
                </div>
                <script>
                    const signInPost = () => {
                        const unameInput = document.querySelector('input[name="uname"]')
                        const pswInput = document.querySelector('input[name="psw"]')
                        
                        const data = {
                            'login': unameInput.value,
                            'password': pswInput.value
                        }
                        
                        fetch('http://localhost:8000/api/users/sign-in', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            redirect: 'follow',
                            body: JSON.stringify(data)
                        }).then(async res => {
                            console.log(res)
                            console.log(await res.json())
                        })
                    }
                </script>
            </body>
        </html>
    """
    return HTMLResponse(content)


@router.get('/sign-up')
def sign_up(token: Token = None):
    if token:
        return RedirectResponse('/', status.HTTP_302_FOUND)
    content = """
        <html>
            <head>
                <title>Sign Up Page</title>
            </head>
            <body>
                <h1>Please sign up</h1>
                <div>
                    <label for="uname"><b>Username</b></label>
                    <input type="text" placeholder="Enter Username" name="uname" required>
                    
                    <label for="psw"><b>Password</b></label>
                    <input type="password" placeholder="Enter Password" name="psw" required>
                    
                    <button type="submit" onclick="signUpPost()">Sign Up</button>
                </div>
                <script>
                    const signUpPost = () => {
                        const unameInput = document.querySelector('input[name="uname"]')
                        const pswInput = document.querySelector('input[name="psw"]')
                        
                        const data = {
                            'login': unameInput.value,
                            'password': pswInput.value
                        }
                        
                        fetch('http://localhost:8000/api/users/sign-up', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            redirect: 'follow',
                            body: JSON.stringify(data)
                        }).then(console.log)
                    }
                </script>
            </body>
        </html>
    """
    return HTMLResponse(content)


@router.get('/')
def root(token: Token = None):
    if not token:
        return RedirectResponse('/sign-in', status.HTTP_302_FOUND)
    content = """
        <html>
            <head>
                <title>Main Page</title>
            </head>
            <body>
                <h1>Welcome to root!</h1>
                <button type="submit" onclick="signOut()">Sign Out</button>
            </body>
            <script>
            const signOut = () => {
                fetch('http://localhost:8000/api/users/sign-out', {method: 'POST'})
                .then(console.log)
            }
            </script>
        </html>
    """
    return HTMLResponse(content)
