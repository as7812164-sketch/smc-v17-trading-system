.class public interface abstract Lb/b;
.super Ljava/lang/Object;
.source "SourceFile"

# interfaces
.implements Landroid/os/IInterface;


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lb/b$b;,
        Lb/b$a;
    }
.end annotation


# static fields
.field public static final d:Ljava/lang/String;


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
    const-string v2, "android$support$customtabs$trusted$ITrustedWebActivityService"

    .line 6
    .line 7
    invoke-virtual {v2, v0, v1}, Ljava/lang/String;->replace(CC)Ljava/lang/String;

    .line 8
    .line 9
    .line 10
    move-result-object v0

    .line 11
    sput-object v0, Lb/b;->d:Ljava/lang/String;

    .line 12
    .line 13
    return-void
.end method


# virtual methods
.method public abstract c()Landroid/os/Bundle;
.end method

.method public abstract i()I
.end method

.method public abstract j(Landroid/os/Bundle;)V
.end method

.method public abstract m(Landroid/os/Bundle;)Landroid/os/Bundle;
.end method

.method public abstract n()Landroid/os/Bundle;
.end method

.method public abstract p(Landroid/os/Bundle;)Landroid/os/Bundle;
.end method

.method public abstract u(Ljava/lang/String;Landroid/os/Bundle;Landroid/os/IBinder;)Landroid/os/Bundle;
.end method
