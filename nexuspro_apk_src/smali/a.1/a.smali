.class public interface abstract La/a;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroid/os/IInterface;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        La/a$b;,
        La/a$a;
    }
.end annotation


# static fields
.field public static final a:Ljava/lang/String;


# direct methods
.method static constructor <clinit>()V
    .locals 3

    .line 1
    const/16 v0, 0x24

    .line 2
    .line 3
    const/16 v1, 0x2e

    .line 4
    .line 5
    const-string v2, "android$support$customtabs$ICustomTabsCallback"

    .line 6
    .line 7
    invoke-virtual {v2, v0, v1}, Ljava/lang/String;->replace(CC)Ljava/lang/String;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    sput-object v0, La/a;->a:Ljava/lang/String;

    .line 12
    .line 13
    return-void
.end method


# virtual methods
.method public abstract a(Ljava/lang/String;Landroid/os/Bundle;)V
.end method

.method public abstract d(Ljava/lang/String;Landroid/os/Bundle;)V
.end method

.method public abstract f(IIIIILandroid/os/Bundle;)V
.end method

.method public abstract g(Landroid/os/Bundle;)V
.end method

.method public abstract h(IILandroid/os/Bundle;)V
.end method

.method public abstract l(Ljava/lang/String;Landroid/os/Bundle;)Landroid/os/Bundle;
.end method

.method public abstract o(ILandroid/net/Uri;ZLandroid/os/Bundle;)V
.end method

.method public abstract r(Landroid/os/Bundle;)V
.end method

.method public abstract s(Landroid/os/Bundle;)V
.end method

.method public abstract v(Landroid/os/Bundle;)V
.end method

.method public abstract w(ILandroid/os/Bundle;)V
.end method
