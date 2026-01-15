; P4V AI Assistant - NSIS Installer Script
; Requires NSIS 3.0+

;--------------------------------
; Includes

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

;--------------------------------
; Version Info (must be before Name)

!define VERSION "0.4.0"
!define PUBLISHER "Netmarble Neo"

;--------------------------------
; General

Name "P4V AI Assistant ${VERSION}"
OutFile "..\dist\P4V-AI-Assistant-Setup.exe"
InstallDir "$PROGRAMFILES\P4V-AI-Assistant"
InstallDirRegKey HKLM "Software\P4V-AI-Assistant" "InstallDir"
RequestExecutionLevel admin
Unicode True

VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "P4V AI Assistant"
VIAddVersionKey "CompanyName" "${PUBLISHER}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "FileDescription" "P4V AI Assistant Installer"
VIAddVersionKey "LegalCopyright" "Copyright (c) 2026 ${PUBLISHER}"

;--------------------------------
; Variables

Var WebhookURL
Var Dialog
Var Label
Var Text

;--------------------------------
; Interface Settings

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

;--------------------------------
; Pages

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
Page custom WebhookPage WebhookPageLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Webhook URL Custom Page

Function WebhookPage
    !insertmacro MUI_HEADER_TEXT "n8n Webhook Configuration" "Enter your n8n Webhook URL for AI features."

    nsDialogs::Create 1018
    Pop $Dialog

    ${If} $Dialog == error
        Abort
    ${EndIf}

    ${NSD_CreateLabel} 0 0 100% 24u "Enter your n8n Webhook URL:$\n(e.g., https://your-n8n-server.com/webhook/xxxxx)"
    Pop $Label

    ${NSD_CreateText} 0 30u 100% 12u "https://n8n-nos.nmn.io/webhook/p4v-ai-assistant"
    Pop $Text

    ${NSD_CreateLabel} 0 50u 100% 36u "* You can change the Webhook URL later in Settings.$\n* If you skip this, you'll need to configure it on first run."
    Pop $Label

    nsDialogs::Show
FunctionEnd

Function WebhookPageLeave
    ${NSD_GetText} $Text $WebhookURL
FunctionEnd

;--------------------------------
; Installer Section

Section "Install" SecInstall
    SetOutPath "$INSTDIR"

    ; Copy main executable
    File "..\dist\p4v_ai_assistant.exe"

    ; Create config directory and file
    CreateDirectory "$APPDATA\P4V-AI-Assistant"

    ; Write config.json if webhook URL provided
    ${If} $WebhookURL != ""
        FileOpen $0 "$APPDATA\P4V-AI-Assistant\config.json" w
        FileWrite $0 '{"webhook_url": "$WebhookURL", "timeout": 60, "language": "ko", "expert_profile": "generic", "custom_prompts": {"description": "", "review": ""}}'
        FileClose $0
    ${EndIf}

    ; Register with P4V Custom Tools
    nsExec::ExecToLog '"$INSTDIR\p4v_ai_assistant.exe" install'

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\P4V AI Assistant"
    CreateShortcut "$SMPROGRAMS\P4V AI Assistant\Settings.lnk" "$INSTDIR\p4v_ai_assistant.exe" "settings"
    CreateShortcut "$SMPROGRAMS\P4V AI Assistant\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Write registry keys for Add/Remove Programs
    WriteRegStr HKLM "Software\P4V-AI-Assistant" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "DisplayName" "P4V AI Assistant"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "DisplayVersion" "${VERSION}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "NoRepair" 1

    ; Get installed size
    ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
    IntFmt $0 "0x%08X" $0
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant" "EstimatedSize" "$0"

SectionEnd

;--------------------------------
; Uninstaller Section

Section "Uninstall"
    ; Unregister from P4V Custom Tools
    nsExec::ExecToLog '"$INSTDIR\p4v_ai_assistant.exe" uninstall'

    ; Remove files
    Delete "$INSTDIR\p4v_ai_assistant.exe"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"

    ; Remove Start Menu shortcuts
    Delete "$SMPROGRAMS\P4V AI Assistant\Settings.lnk"
    Delete "$SMPROGRAMS\P4V AI Assistant\Uninstall.lnk"
    RMDir "$SMPROGRAMS\P4V AI Assistant"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\P4V-AI-Assistant"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\P4V-AI-Assistant"

    ; Note: We don't delete config in APPDATA to preserve user settings

SectionEnd
