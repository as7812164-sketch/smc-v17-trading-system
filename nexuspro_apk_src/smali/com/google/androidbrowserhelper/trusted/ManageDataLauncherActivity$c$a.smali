.class Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;
.super Ln/b;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;


# direct methods
.method constructor <init>(Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;)V
    .locals 0

    .line 1
    iput-object p1, p0, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;->a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;

    .line 2
    .line 3
    invoke-direct {p0}, Ln/b;-><init>()V

    .line 4
    .line 5
    .line 6
    return-void
.end method


# virtual methods
.method public i(ILandroid/net/Uri;ZLandroid/os/Bundle;)V
    .locals 1

    .line 1
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;->a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;

    .line 2
    .line 3
    iget-object p1, p1, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;->d:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;

    .line 4
    .line 5
    invoke-virtual {p1}, Landroid/app/Activity;->isFinishing()Z

    .line 6
    .line 7
    .line 8
    move-result p1

    .line 9
    if-eqz p1, :cond_0

    .line 10
    .line 11
    return-void

    .line 12
    :cond_0
    if-nez p3, :cond_1

    .line 13
    .line 14
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;->a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;

    .line 15
    .line 16
    iget-object p1, p1, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;->d:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;

    .line 17
    .line 18
    new-instance p3, Ljava/lang/RuntimeException;

    .line 19
    .line 20
    new-instance p4, Ljava/lang/StringBuilder;

    .line 21
    .line 22
    invoke-direct {p4}, Ljava/lang/StringBuilder;-><init>()V

    .line 23
    .line 24
    .line 25
    const-string v0, "Failed to validate origin "

    .line 26
    .line 27
    invoke-virtual {p4, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 28
    .line 29
    .line 30
    invoke-virtual {p4, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    .line 31
    .line 32
    .line 33
    invoke-virtual {p4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    .line 34
    .line 35
    .line 36
    move-result-object p2

    .line 37
    invoke-direct {p3, p2}, Ljava/lang/RuntimeException;-><init>(Ljava/lang/String;)V

    .line 38
    .line 39
    .line 40
    invoke-virtual {p1, p3}, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;->j(Ljava/lang/RuntimeException;)V

    .line 41
    .line 42
    .line 43
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;->a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;

    .line 44
    .line 45
    iget-object p1, p1, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;->d:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;

    .line 46
    .line 47
    invoke-virtual {p1}, Landroid/app/Activity;->finish()V

    .line 48
    .line 49
    .line 50
    return-void

    .line 51
    :cond_1
    iget-object p1, p0, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c$a;->a:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;

    .line 52
    .line 53
    iget-object p2, p1, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;->d:Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;

    .line 54
    .line 55
    invoke-static {p1}, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;->c(Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity$c;)Ln/f;

    .line 56
    .line 57
    .line 58
    move-result-object p1

    .line 59
    invoke-static {p2, p1}, Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;->a(Lcom/google/androidbrowserhelper/trusted/ManageDataLauncherActivity;Ln/f;)V

    .line 60
    .line 61
    .line 62
    return-void
.end method
