<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Admin</%def>
<%inherit file="base.mako"/>
        ${self.logo()}
        <br/>
        <h2>Documentation</h2>
        <p>
        Most of CheckMeIn is designed to be used only with the webapp. However,
        there are a few endpoints that other systems can interact with.
        </p>
% for doc in docs:
        <details>
            <summary>${doc.summary}</summary>
            <pre><code>${doc.code}</code></pre>
            <ul>
  % for note in doc.notes:
                <li>${note}</li>
  % endfor
            </ul>
            <p><b>Returns:</b> ${doc.returns}</p>
        </details>
% endfor
        <hr/>
        To add feature requests or report issues, please go to:
        <a href="{repo}/issues">${repo}/issues</a>
