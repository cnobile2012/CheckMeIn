<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Login</%def>
<%inherit file="base.mako"/>
${self.logo()}
        <br/>
        <h1>Login Page</h1>
        <form action="login_attempt">
            <fieldset>
                <legend>Login</legend>
                <input id="user_id" type="text" name="username"
                       placeholder="Login Name" />
                <br />
                <input id="pass_id" class="password" type="password"
                       name="password" placeholder="Password" />
                <br />
                <input type="submit" value="Login"/>
            </fieldset>
        </form>
        <form action="forgot_password">
            <fieldset>
                <legend>Forgot Password</legend>
                If you do not remember your user name, you can enter your
                email and we can find your user profile with that as well.
                <br/>
                <input id="user_id" type="text" name="user"
                       placeholder="Login Name" />
                <br />
                <input type="submit" value="Forgot password"/>
            </fieldset>
        </form>
