.class LL/f;
.super Ljava/lang/Object;
.source "SourceFile"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        LL/f$b;
    }
.end annotation


# instance fields
.field private a:Ljava/util/Map;


# direct methods
.method constructor <init>()V
    .locals 1

    .line 1
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 2
    .line 3
    .line 4
    new-instance v0, Ljava/util/HashMap;

    .line 5
    .line 6
    invoke-direct {v0}, Ljava/util/HashMap;-><init>()V

    .line 7
    .line 8
    .line 9
    iput-object v0, p0, LL/f;->a:Ljava/util/Map;

    .line 10
    .line 11
    return-void
.end method

.method private static a(Landroid/content/Context;Lo/q;)I
    .locals 1

    .line 1
    invoke-virtual {p1}, Lo/q;->b()Ln/d;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    iget-object p1, p1, Ln/d;->a:Landroid/content/Intent;

    .line 6
    .line 7
    invoke-virtual {p1}, Landroid/content/Intent;->getExtras()Landroid/os/Bundle;

    .line 8
    .line 9
    .line 10
    move-result-object p1

    .line 11
    if-nez p1, :cond_0

    .line 12
    .line 13
    const/4 p1, 0x0

    .line 14
    goto :goto_0

    .line 15
    :cond_0
    const-string v0, "androidx.browser.customtabs.extra.COLOR_SCHEME"

    .line 16
    .line 17
    invoke-virtual {p1, v0}, Landroid/os/BaseBundle;->get(Ljava/lang/String;)Ljava/lang/Object;

    .line 18
    .line 19
    .line 20
    move-result-object p1

    .line 21
    check-cast p1, Ljava/lang/Integer;

    .line 22
    .line 23
    :goto_0
    if-eqz p1, :cond_1

    .line 24
    .line 25
    invoke-virtual {p1}, Ljava/lang/Integer;->intValue()I

    .line 26
    .line 27
    .line 28
    move-result v0

    .line 29
    if-eqz v0, :cond_1

    .line 30
    .line 31
    invoke-virtual {p1}, Ljava/lang/Integer;->intValue()I

    .line 32
    .line 33
    .line 34
    move-result p0

    .line 35
    return p0

    .line 36
    :cond_1
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    .line 37
    .line 38
    .line 39
    move-result-object p0

    .line 40
    invoke-virtual {p0}, Landroid/content/res/Resources;->getConfiguration()Landroid/content/res/Configuration;

    .line 41
    .line 42
    .line 43
    move-result-object p0

    .line 44
    iget p0, p0, Landroid/content/res/Configuration;->uiMode:I

    .line 45
    .line 46
    and-int/lit8 p0, p0, 0x30

    .line 47
    .line 48
    const/16 p1, 0x20

    .line 49
    .line 50
    if-ne p0, p1, :cond_2

    .line 51
    .line 52
    const/4 p0, 0x2

    .line 53
    return p0

    .line 54
    :cond_2
    const/4 p0, 0x1

    .line 55
    return p0
.end method

.method private d(Landroid/content/Context;Ljava/lang/String;)LL/f$b;
    .locals 4

    .line 1
    iget-object v0, p0, LL/f;->a:Ljava/util/Map;

    .line 2
    .line 3
    invoke-interface {v0, p2}, Ljava/util/Map;->get(Ljava/lang/Object;)Ljava/lang/Object;

    .line 4
    .line 5
    .line 6
    move-result-object v0

    .line 7
    check-cast v0, LL/f$b;

    .line 8
    .line 9
    if-eqz v0, :cond_0

    .line 10
    .line 11
    return-object v0

    .line 12
    :cond_0
    invoke-virtual {p1}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 13
    .line 14
    .line 15
    move-result-object v0

    .line 16
    invoke-static {v0, p2}, LK/b;->e(Landroid/content/pm/PackageManager;Ljava/lang/String;)Z

    .line 17
    .line 18
    .line 19
    move-result v0

    .line 20
    const/4 v1, 0x0

    .line 21
    if-eqz v0, :cond_1

    .line 22
    .line 23
    new-instance p1, LL/f$b;

    .line 24
    .line 25
    const/4 v0, 0x1

    .line 26
    invoke-direct {p1, v0, v0, v1}, LL/f$b;-><init>(ZZLL/f$a;)V

    .line 27
    .line 28
    .line 29
    iget-object v0, p0, LL/f;->a:Ljava/util/Map;

    .line 30
    .line 31
    invoke-interface {v0, p2, p1}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 32
    .line 33
    .line 34
    return-object p1

    .line 35
    :cond_1
    new-instance v0, Landroid/content/Intent;

    .line 36
    .line 37
    invoke-direct {v0}, Landroid/content/Intent;-><init>()V

    .line 38
    .line 39
    .line 40
    const-string v2, "android.support.customtabs.action.CustomTabsService"

    .line 41
    .line 42
    invoke-virtual {v0, v2}, Landroid/content/Intent;->setAction(Ljava/lang/String;)Landroid/content/Intent;

    .line 43
    .line 44
    .line 45
    move-result-object v0

    .line 46
    invoke-virtual {v0, p2}, Landroid/content/Intent;->setPackage(Ljava/lang/String;)Landroid/content/Intent;

    .line 47
    .line 48
    .line 49
    move-result-object v0

    .line 50
    invoke-virtual {p1}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;

    .line 51
    .line 52
    .line 53
    move-result-object p1

    .line 54
    const/16 v2, 0x40

    .line 55
    .line 56
    invoke-virtual {p1, v0, v2}, Landroid/content/pm/PackageManager;->resolveService(Landroid/content/Intent;I)Landroid/content/pm/ResolveInfo;

    .line 57
    .line 58
    .line 59
    move-result-object p1

    .line 60
    new-instance v0, LL/f$b;

    .line 61
    .line 62
    const-string v2, "androidx.browser.customtabs.category.NavBarColorCustomization"

    .line 63
    .line 64
    invoke-static {p1, v2}, LL/f;->e(Landroid/content/pm/ResolveInfo;Ljava/lang/String;)Z

    .line 65
    .line 66
    .line 67
    move-result v2

    .line 68
    const-string v3, "androidx.browser.customtabs.category.ColorSchemeCustomization"

    .line 69
    .line 70
    invoke-static {p1, v3}, LL/f;->e(Landroid/content/pm/ResolveInfo;Ljava/lang/String;)Z

    .line 71
    .line 72
    .line 73
    move-result p1

    .line 74
    invoke-direct {v0, v2, p1, v1}, LL/f$b;-><init>(ZZLL/f$a;)V

    .line 75
    .line 76
    .line 77
    iget-object p1, p0, LL/f;->a:Ljava/util/Map;

    .line 78
    .line 79
    invoke-interface {p1, p2, v0}, Ljava/util/Map;->put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;

    .line 80
    .line 81
    .line 82
    return-object v0
.end method

.method private static e(Landroid/content/pm/ResolveInfo;Ljava/lang/String;)Z
    .locals 0

    .line 1
    if-eqz p0, :cond_0

    .line 2
    .line 3
    iget-object p0, p0, Landroid/content/pm/ResolveInfo;->filter:Landroid/content/IntentFilter;

    .line 4
    .line 5
    if-eqz p0, :cond_0

    .line 6
    .line 7
    invoke-virtual {p0, p1}, Landroid/content/IntentFilter;->hasCategory(Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result p0

    .line 11
    if-eqz p0, :cond_0

    .line 12
    .line 13
    const/4 p0, 0x1

    .line 14
    return p0

    .line 15
    :cond_0
    const/4 p0, 0x0

    .line 16
    return p0
.end method

.method private f(Landroid/content/Context;Ljava/lang/String;)Z
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, LL/f;->d(Landroid/content/Context;Ljava/lang/String;)LL/f$b;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    iget-boolean p1, p1, LL/f$b;->b:Z

    .line 6
    .line 7
    return p1
.end method

.method private g(Landroid/content/Context;Ljava/lang/String;)Z
    .locals 0

    .line 1
    invoke-direct {p0, p1, p2}, LL/f;->d(Landroid/content/Context;Ljava/lang/String;)LL/f$b;

    .line 2
    .line 3
    .line 4
    move-result-object p1

    .line 5
    iget-boolean p1, p1, LL/f$b;->a:Z

    .line 6
    .line 7
    return p1
.end method


# virtual methods
.method b(Landroid/content/Context;Ljava/lang/String;Lo/q;)Ljava/lang/Integer;
    .locals 3

    .line 1
    invoke-virtual {p3}, Lo/q;->b()Ln/d;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    iget-object v0, v0, Ln/d;->a:Landroid/content/Intent;

    .line 6
    .line 7
    invoke-direct {p0, p1, p2}, LL/f;->g(Landroid/content/Context;Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result v1

    .line 11
    const/4 v2, 0x0

    .line 12
    if-eqz v1, :cond_2

    .line 13
    .line 14
    invoke-direct {p0, p1, p2}, LL/f;->f(Landroid/content/Context;Ljava/lang/String;)Z

    .line 15
    .line 16
    .line 17
    move-result p2

    .line 18
    if-eqz p2, :cond_0

    .line 19
    .line 20
    invoke-static {p1, p3}, LL/f;->a(Landroid/content/Context;Lo/q;)I

    .line 21
    .line 22
    .line 23
    move-result p1

    .line 24
    invoke-static {v0, p1}, Ln/d;->a(Landroid/content/Intent;I)Ln/a;

    .line 25
    .line 26
    .line 27
    move-result-object p1

    .line 28
    iget-object p1, p1, Ln/a;->c:Ljava/lang/Integer;

    .line 29
    .line 30
    return-object p1

    .line 31
    :cond_0
    invoke-virtual {v0}, Landroid/content/Intent;->getExtras()Landroid/os/Bundle;

    .line 32
    .line 33
    .line 34
    move-result-object p1

    .line 35
    if-nez p1, :cond_1

    .line 36
    .line 37
    return-object v2

    .line 38
    :cond_1
    const-string p2, "androidx.browser.customtabs.extra.NAVIGATION_BAR_COLOR"

    .line 39
    .line 40
    invoke-virtual {p1, p2}, Landroid/os/BaseBundle;->get(Ljava/lang/String;)Ljava/lang/Object;

    .line 41
    .line 42
    .line 43
    move-result-object p1

    .line 44
    check-cast p1, Ljava/lang/Integer;

    .line 45
    .line 46
    return-object p1

    .line 47
    :cond_2
    invoke-static {p2}, LK/b;->h(Ljava/lang/String;)Z

    .line 48
    .line 49
    .line 50
    move-result p1

    .line 51
    if-eqz p1, :cond_3

    .line 52
    .line 53
    const/4 p1, -0x1

    .line 54
    invoke-static {p1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    .line 55
    .line 56
    .line 57
    move-result-object p1

    .line 58
    return-object p1

    .line 59
    :cond_3
    return-object v2
.end method

.method c(Landroid/content/Context;Ljava/lang/String;Lo/q;)Ljava/lang/Integer;
    .locals 1

    .line 1
    invoke-virtual {p3}, Lo/q;->b()Ln/d;

    .line 2
    .line 3
    .line 4
    move-result-object v0

    .line 5
    iget-object v0, v0, Ln/d;->a:Landroid/content/Intent;

    .line 6
    .line 7
    invoke-direct {p0, p1, p2}, LL/f;->f(Landroid/content/Context;Ljava/lang/String;)Z

    .line 8
    .line 9
    .line 10
    move-result p2

    .line 11
    if-eqz p2, :cond_0

    .line 12
    .line 13
    invoke-static {p1, p3}, LL/f;->a(Landroid/content/Context;Lo/q;)I

    .line 14
    .line 15
    .line 16
    move-result p1

    .line 17
    invoke-static {v0, p1}, Ln/d;->a(Landroid/content/Intent;I)Ln/a;

    .line 18
    .line 19
    .line 20
    move-result-object p1

    .line 21
    iget-object p1, p1, Ln/a;->a:Ljava/lang/Integer;

    .line 22
    .line 23
    return-object p1

    .line 24
    :cond_0
    invoke-virtual {v0}, Landroid/content/Intent;->getExtras()Landroid/os/Bundle;

    .line 25
    .line 26
    .line 27
    move-result-object p1

    .line 28
    if-nez p1, :cond_1

    .line 29
    .line 30
    const/4 p1, 0x0

    .line 31
    return-object p1

    .line 32
    :cond_1
    const-string p2, "android.support.customtabs.extra.TOOLBAR_COLOR"

    .line 33
    .line 34
    invoke-virtual {p1, p2}, Landroid/os/BaseBundle;->get(Ljava/lang/String;)Ljava/lang/Object;

    .line 35
    .line 36
    .line 37
    move-result-object p1

    .line 38
    check-cast p1, Ljava/lang/Integer;

    .line 39
    .line 40
    return-object p1
.end method
